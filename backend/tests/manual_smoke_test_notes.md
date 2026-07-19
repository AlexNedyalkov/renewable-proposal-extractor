# Task 10 — Manual Smoke Test Notes

## What was tested

Full pipeline, no mocks: `POST /api/documents` → PDF text extraction
(pdfplumber) → Claude extraction (real Anthropic API call) → normalization →
in-memory storage → JSON response. Both smoke tests below are automated but
opt-in (`@pytest.mark.live` in `test_documents_endpoint_live.py`, excluded
from default `pytest` runs; run explicitly with `pytest -m live`).

## Part 1: Real-world documents

Five public renewable-energy project financing documents ("Report and
Recommendation of the President" filings) were downloaded from the Asian
Development Bank — the closest real analogue available to the kind of
proposal TerraWatt's analysts review — and saved to
`backend/tests/fixtures/real_samples/`:

| File | Project | Tech |
| --- | --- | --- |
| ac_energy_wind_vietnam.pdf | AC Energy Wind Power Project | Onshore wind |
| monsoon_wind_laos.pdf | Monsoon Wind Power Project | Onshore wind |
| triconboston_wind.pdf | Triconboston Wind Power Project | Onshore wind |
| aj_solar_india.pdf | AJ Solar Power Project | Solar PV |
| cambodia_solar.pdf | Cambodia Solar Power Project | Solar PV |

All 5 returned `200 OK` with a populated `ProposalExtraction`.

### Technical fields: consistently strong

`project_name`, `location`, `technology_type`, `installed_capacity_mw`,
`expected_annual_generation_mwh`, `commercial_operation_date`, and
`developer_sponsor` were extracted at **high confidence, correctly, in all 5
documents** — these facts are typically stated plainly in prose near the top
of each document, and the model located them reliably regardless of layout.

### Financial fields: honest gaps, not hallucination

This is the more interesting result. `expected_irr_percent`,
`payback_period_years`, and `lcoe_usd_per_mwh` came back `not_found` in
**all 5** real documents — these institutional financing documents don't
state them as clean, quotable prose the way a private-equity teaser might;
the underlying numbers exist in financial model appendices/tables that
either weren't in the extracted text cleanly or are structured differently
per document. `total_capex_usd` was found in 2 of 5 (Triconboston,
Cambodia), `not_found` in the other 3, and `debt_equity_ratio` was found in
3 of 5 but in inconsistent formats (`"75:25"`, `"2.94x / 2.24x"`, a currency
amount pair) since the schema doesn't constrain its shape.

Critically, the model did **not fabricate** values for the missing fields —
every miss came back as `null`/`not_found` rather than a plausible-looking
guess. One document (Cambodia) even surfaced *why* a field was missing: for
`expected_irr_percent` the model returned `not_found` with
`source_snippet: "CONFIDENTIAL INFORMATION DELETED."` — it correctly
recognized that the IRR line existed in the source document but had been
redacted, rather than inventing a number in its place. That's the graceful
degradation behavior Task 6 was built to guarantee, holding up against real
documents it was never tuned on.

### Limitation surfaced: no canonical format for compound fields

`debt_equity_ratio` is a free-text field, so real documents produced three
different representations of "the same kind of fact." A production version
of this schema should probably split compound fields like this into
strictly-typed sub-fields (e.g. `debt_percent: float`, `equity_percent:
float`) rather than a loosely-typed string, to make the output reliably
machine-comparable across documents.

## Part 2: Synthetic document (baseline / regression check)

A synthetic multi-page proposal (`Prairie Wind Energy Project`, generated
with fpdf2, all 15 fields stated explicitly in clean prose) was also run
through the pipeline as a controlled baseline: **15/15 fields extracted
correctly at "high" confidence**, each with an accurate `source_snippet`.
This confirms the pipeline's plumbing (upload → extract → LLM → normalize →
store → respond) is correct when the input document is unambiguous — the
gaps seen in Part 1 are about real-world document variance, not a bug in
this codebase.

## Not yet tested

- Scanned/image-only PDFs (would hit `NoExtractableTextError`, already unit
  tested in Task 3/7, but not exercised against a real scanned document).
- Documents long enough to approach Claude's context window limits.
- A document TerraWatt itself considers representative (these ADB filings
  are a reasonable proxy but are development-bank financing documents, not
  private-investor pitch decks — the two may differ in structure/tone).

## Recommendation

Before relying on this for production use, validate against a handful of
TerraWatt's actual proposal documents, and consider splitting
`debt_equity_ratio` (and similarly compound fields) into strictly-typed
numeric sub-fields.

## Update (sprint v3): debt_equity_ratio limitation fixed and re-verified

The "no canonical format" limitation above was fixed in sprint v3: schema
now has strictly-typed `debt_percent`/`equity_percent` numeric fields
instead of free-text `debt_equity_ratio`. Re-ran `pytest -m live` (all 7
live tests pass, ~110s) and additionally captured full responses for the
two most relevant real documents:

- **`triconboston_wind.pdf`** (previously `debt_equity_ratio: "75:25"`):
  now returns `debt_percent: 75` and `equity_percent: 25`, both `high`
  confidence, both citing the same snippet the old field used — the split
  is a clean, lossless improvement over the old string.
- **`cambodia_solar.pdf`** — the harder case. This document contains *two*
  different debt/equity disclosures: a Sources-of-Funds percentage
  breakdown (69% debt / 31% equity) and a separate "Debt-Equity Ratio at
  Completion" leverage multiple (2.94x/2.24x), a different metric
  entirely. The real API correctly returned `debt_percent: 69` and
  `equity_percent: 31` — sourced from the Sources-of-Funds table
  (`"Total Debt 9.8 9.2 69"` / `"1. Equity 3.4 4.1 31"`), not the leverage
  ratio — matching this sprint's independently-verified ground truth
  fixture exactly, both at `high` confidence.

This is a good sign: the schema fix didn't just make the *shape* of the
data cleaner, the model's underlying judgment about *which* number in the
document actually answers "debt_percent" was already sound — it just had
no clean typed field to put a percentage-shaped answer into before.
