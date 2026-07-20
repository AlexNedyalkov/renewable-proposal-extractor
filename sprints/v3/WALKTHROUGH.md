# Sprint v3 — Walkthrough

## Summary

Sprint v3 didn't add new surface area — it closed three concrete gaps that real-world testing in v1/v2 had surfaced: a schema field with no canonical format, no repeatable way to measure extraction accuracy, and a backend endpoint (`GET /api/documents/{id}`) that had existed unused since sprint v1. All three closures were verified against the real Anthropic API and real documents, and the verification work itself caught two more real bugs along the way — a value/confidence inconsistency in `normalize_extraction()`'s edge cases, and a missing `document_id` display that made the new lookup feature unreachable by an actual user.

## Architecture Overview

```
                    multipart/form-data                 GET /api/documents/{id}
   Browser --upload PDF-------------->  POST /api/documents  <--lookup by id-- Browser
      |                                        |                                  |
      |                                        v                                  |
      |                          extract -> Claude -> normalize -> store          |
      |                                        |                                  |
      +<----------- {document_id, extraction} -+----------------------------------+
                (renders via the same renderResults(), whichever path got there)


   (offline, manual -- not part of the running app)
   backend/scripts/evaluate_extraction_accuracy.py
      reads: tests/fixtures/real_samples/*.pdf
             tests/fixtures/ground_truth/*.json   (independently verified, not reused
                                                    from prior LLM outputs)
      calls: extract_text() -> run_extraction() -> normalize_extraction()
             (the exact same functions POST /api/documents uses)
      writes: tests/extraction_accuracy_report.md
```

## Files Created/Modified

### backend/app/schemas.py
**Purpose**: The extraction schema — now 16 fields instead of 15.
**How it works**: `debt_equity_ratio` (a free-text `ExtractedField`) is gone, replaced with `debt_percent` and `equity_percent` (both `ExtractedField`, numeric values expected):
```python
ppa_term_years: ExtractedField
debt_percent: ExtractedField
equity_percent: ExtractedField
```
Real-document testing in sprint v1 found the old field came back in three incompatible shapes across 3 of 5 real documents ("75:25", a currency-amount pair, "2.94x/2.24x") — useless for any consumer trying to compute with it. Because `ProposalExtraction.model_json_schema()` auto-generates the Claude tool's `input_schema` (a decision made back in sprint v1), this fix required zero prompt or LLM-integration code changes — just the schema definition.

### backend/tests/fixtures/ground_truth/*.json (5 new files)
**Purpose**: Hand-verified expected values for each real sample PDF, used by the evaluation script.
**How it works**: Rather than reuse sprint v1's prior LLM outputs as "ground truth" (which would just be testing the model against itself), each fixture was built by independently re-extracting each PDF's text via the backend's own `extract_text()` and grepping for financial keywords. This surfaced a genuinely important finding baked into `cambodia_solar.json`'s `notes` field: that document contains *two different* debt/equity disclosures — a Sources-of-Funds percentage breakdown (69%/31%, the correct source for `debt_percent`/`equity_percent`) and a separate "Debt-Equity Ratio at Completion" leverage multiple (2.94x/2.24x, an unrelated covenant metric) — exactly the ambiguity the schema fix above was designed to resolve. Each fixture also documents *why* certain fields are expected `not_found` (e.g., a document explicitly states an economic IRR but redacts the financial IRR that `expected_irr_percent` is meant to capture — treating the disclosed number as the answer would be a subtly wrong "success").

### backend/tests/test_ground_truth_fixtures.py
**Purpose**: Guards the fixtures against future schema drift.
**How it works**: Asserts that every real sample PDF has a matching fixture, and that every fixture's field set exactly equals `ProposalExtraction.model_fields`. If a future sprint adds or removes a schema field without updating these fixtures, this test fails immediately instead of the evaluation script silently scoring the wrong thing.

### backend/scripts/evaluate_extraction_accuracy.py
**Purpose**: Measures extraction accuracy against the ground truth — a repeatable answer to "how would this system's quality be evaluated in production?"
**Key Functions**: `field_matches()`, `score_document()`, `run_document()`, `main()`

**How it works**:
```python
if not expectation["expected_found"]:
    if not actual_found:
        return True, "correctly not_found"
    return False, f"expected not_found but got value={actual_value!r}"
```
`field_matches()` and `score_document()` are pure functions with zero I/O, fully unit tested without touching the network. `run_document()` wires them to the real pipeline (`extract_text` → `run_extraction` → `normalize_extraction` — the exact same functions the API route uses, called directly rather than through HTTP) and `main()` iterates every ground-truth fixture, aggregating a per-document and overall accuracy figure. One unit test caught a real bug during development: a field entirely *absent* from the extraction dict was being treated as "found" rather than "not_found", because `None != "not_found"` evaluates to `True`. Fixed by checking membership in the actual confidence levels (`"high"`, `"medium"`, `"low"`) instead of inequality with the sentinel.

### backend/tests/extraction_accuracy_report.md
**Purpose**: The actual output of running the script for real (once, against all 5 real documents) — **77/80 fields correct, 96.2% overall**, clearing the project plan's 85%+ target with an 11-point margin. Both misses are investigated and explained rather than glossed over: one is known LLM non-determinism on an already-documented ambiguous field (`triconboston_wind.pdf`'s "17% return on equity" vs. overall IRR); the other revealed that a single raw API call had paired a non-`not_found` confidence with a `null` value — an internally inconsistent combination the schema doesn't currently forbid, confirmed as a one-off via a follow-up call and flagged as a concrete `normalize_extraction()` hardening opportunity for later.

### frontend/index.html, frontend/app.js
**Purpose**: Adds a "look up a previous analysis by ID" path into the existing results view, plus a document-ID display that makes that feature actually reachable.
**How it works**: The lookup form's submit handler is almost a mirror of the upload handler:
```js
const response = await fetch(`/api/documents/${encodeURIComponent(documentId)}`);
const data = await response.json();
if (response.ok) {
  showDocumentId(data.document_id);
  renderResults(data.extraction);
} else {
  showErrorBanner(data?.detail?.message || 'An unexpected error occurred.');
}
```
Both paths call the exact same `renderResults()`/`showErrorBanner()` helpers, so there's only one rendering code path to keep correct, not two. No backend changes were needed — `GET /api/documents/{id}` has existed since sprint v1 with nothing calling it. While verifying this end-to-end (Task 8), it became clear the UI never actually *displayed* `document_id` after an upload — so a real analyst had no way to copy an ID to look up later, making the whole feature practically unreachable despite being "done." Fixed by adding a `document-id-value` display, shown after both upload and lookup.

### API_CONTRACT.md, e2e fixtures (results-view.spec.ts, responsive-empty-state.spec.ts)
**Purpose**: Keep documentation and test fixtures honest about the current schema.
**How it works**: No new application behavior — pure accuracy fixes, verified by re-running the existing suites rather than a red/green cycle (the same category as sprint v1's API-contract-documentation task). `API_CONTRACT.md` gained a "Schema change (sprint v3)" section explaining the field replacement; historical sprint documents (v1/v2 PRDs, TASKS, WALKTHROUGHs) were deliberately left referencing the old field name, since they're point-in-time snapshots of what was true when written, not living documents.

## Data Flow

**Lookup path** (new): User enters a document ID → `fetch GET /api/documents/{id}` → on `200`, `document_id` is displayed and `renderResults()` runs — the identical function the upload path uses → on `404`, the existing error-banner pattern shows the not-found message.

**Evaluation path** (new, offline): `evaluate_extraction_accuracy.py` reads each ground-truth fixture → runs the real pipeline directly (no HTTP) against the matching real sample PDF → `score_document()` compares every field → results aggregate into a report.

## Test Coverage

- **Backend unit**: 40 tests in the default suite (up from 30 at the start of this sprint) — added 9 for the evaluation script's comparison logic and pipeline wiring, plus 2 for ground-truth fixture structure.
- **Backend live (opt-in)**: 7 tests, unchanged in count but re-verified — confirmed `debt_percent`/`equity_percent` populate correctly on the real API for both a simple case (`triconboston_wind.pdf`, 75/25) and the ambiguous case (`cambodia_solar.pdf`, 69/31, correctly avoiding the unrelated leverage-ratio metric).
- **E2E (Playwright, mocked)**: 16 total tests across 8 spec files, 14 run by default — added 4 for the lookup-by-id feature (found, not-found, document-ID display, plus type-checking via `tsc --noEmit`).
- **E2E (Playwright, live, opt-in)**: 2 tests now (was 1) — added the real lookup-by-id round-trip verification (upload live, capture the real ID, reload, look it up, confirm matching data).
- **Manual/documented**: the extraction-accuracy evaluation run itself (77/80, 96.2%) isn't a pass/fail test — it's a measurement, intentionally reported with its caveats rather than treated as a gate.

## Security Measures

- No new dependencies introduced anywhere in this sprint (backend or frontend) — `pip-audit` and `npm audit` stayed clean throughout with zero new packages.
- `semgrep --config auto` clean after every task.
- The document ID entered by a user is `encodeURIComponent`-escaped before being built into the lookup fetch URL.
- No secrets or credentials touched; `ANTHROPIC_API_KEY` handling is unchanged from prior sprints.

## Known Limitations

- **`normalize_extraction()` doesn't yet reject a `null` value paired with a non-`not_found` confidence** — observed once during the Task 7 evaluation run (see `extraction_accuracy_report.md`), not reproduced on a follow-up call, but the schema doesn't structurally forbid it. Flagged as a concrete fix for later, not done this sprint (would have been scope creep on a verification task).
- **The evaluation harness's ground truth covers only 5 documents** — 96.2% is an encouraging snapshot, not a statistically robust accuracy estimate. It's also not perfectly reproducible run-to-run for genuinely ambiguous fields, which is itself an honest and useful thing to know about this system's behavior.
- **Lookup-by-id has no persistence beyond the process lifetime** — inherited from sprint v1's in-memory store; a document ID is only useful until the server restarts.
- **No full history/list view** — still just single-ID lookup, as scoped; a `GET /api/documents` list endpoint would be needed for that and was explicitly deferred again this sprint.
- **README.md and the AI-assistant conversation log are still outstanding** — both required deliverables per the brief, still deliberately deferred by the user to the end of the project rather than any specific sprint.

## What's Next

- Whenever the project is being wrapped up: README.md and the AI conversation log.
- Consider the `normalize_extraction()` hardening noted above.
- Expand the ground-truth set beyond 5 documents if more real (ideally TerraWatt-provided) proposals become available, and re-run the evaluation script whenever the prompt, schema, or model changes to track accuracy as a trend rather than a single number.
- If a history/list view becomes a priority, it will need a new `GET /api/documents` backend endpoint — out of scope for both v2 and v3 so far.
