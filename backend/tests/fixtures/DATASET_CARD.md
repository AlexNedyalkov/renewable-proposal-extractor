# Dataset Card — Renewable Proposal Extraction Eval

The "answer key" the extractor is scored against. Goal: a trustworthy, diverse, **held-out**
22-doc set (10 dev / 12 test), with ground truth built by **independent multi-model
annotation** (Option B). This card is the **annotation protocol** — the rules every annotator
follows so the ground truth is consistent. *(Sprint v5, Task 1.)*

---

## 1. Ground-truth record format

One file per doc → `tests/fixtures/ground_truth/<name>.json`:

```json
{
  "source_pdf": "<name>.pdf",
  "split": "dev" | "test",
  "fields": {
    "<field_name>": {
      "expected_found": true,
      "expected_value": 150,
      "match": "numeric",
      "notes": "Stated as '150 MW' (solar PV). Source quote + any conversion/decision."
    }
  }
}
```

- **`expected_value` is a *bare* value** — the unit / `%` lives in the **field name**, never in
  the value (`150`, not `"150 MW"`; `70`, not `"70%"`).
- **`notes` always quotes the source text** so a human can verify, and records any conversion
  or judgment call.
- If not present in the doc: `expected_found: false`, `expected_value: null`.

## 2. Match-strategy catalog

| `match` | How it compares | Use for |
|---|---|---|
| `exact` | identical values | codes / exact strings (rare) |
| `contains` | expected text appears within the answer (case-insensitive) | names, location, technology, developer |
| `date` | **parse both sides to a date, compare the dates** (format-agnostic) | `commercial_operation_date` |
| `numeric` | compare as **numbers** with ~1% relative tolerance (tunable per field) | all quantities |

- **`numeric`** forgives rounding (`149.6 ≈ 150` passes) but catches real errors (`140 ≠ 150`).
- **`date`** fixes the format bug we found: `"2027-09-30"` == `"30 September 2027"`. Dates are
  stored as **ISO 8601** (`YYYY-MM-DD`); partial dates at the stated precision (`"2027-09"`).

## 3. Annotation rules

1. **Canonical units.** Record in the field's unit, converting as needed — GW/kW → MW,
   GWh → MWh, `$/kWh → $/MWh (×1000)`, "$180 million" → `180000000`. Note the conversion.
2. **Bare values.** Number/string only; unit or `%` is in the field name.
3. **Dates → ISO 8601.** Prefer the **actual** COD over scheduled/expected; note AC vs DC for
   capacity when the doc specifies.
4. **🔑 Ground truth encodes the extractor's *current* policy.** Never let the answer key
   expect a value the extractor is instructed **not** to produce — that causes systematic
   false-misses (cf. `capex_per_mw`). When the extractor's policy changes (e.g. we build a new
   deriver), **revisit** the affected fixtures.

## 4. Field-specific rules

| Field | `match` | Rule / ambiguity |
|---|---|---|
| project_name | contains | the project's own name — not developer/lender |
| location | contains | country + region if stated |
| technology_type | contains | solar PV / onshore wind / offshore wind / hydro / BESS |
| installed_capacity_mw | numeric | MW (convert GW/kW); **note AC vs DC** when stated |
| expected_annual_generation_mwh | numeric | MWh (convert GWh) |
| commercial_operation_date | date | ISO 8601; **prefer actual over scheduled** |
| developer_sponsor | contains | developer/sponsor — not lender or offtaker |
| total_capex_usd | numeric | USD (expand millions/billions); prefer actual over estimate |
| capex_per_mw | numeric | **Derived in code** (= total_capex ÷ capacity). GT = the derived value when both inputs are known (or the stated value if given directly); else `not_found`. *(Extractor now derives this, so GT may expect it — consistent.)* |
| expected_irr_percent | numeric | **project-level IRR only.** "return on equity" / economic IRR / WACC ≠ this → `not_found` if only those are stated |
| payback_period_years | numeric | years |
| lcoe_usd_per_mwh | numeric | USD/MWh (convert $/kWh). A **cost** — not the PPA price |
| ppa_price_usd_per_mwh | numeric | USD/MWh (convert $/kWh). A **sale price** — not LCOE |
| ppa_term_years | numeric | years — not the loan tenor |
| debt_percent | numeric | stated as **%** → record; only a **ratio/multiple** (e.g. 2.33x) → `not_found` + note the ratio |
| equity_percent | numeric | mirror of `debt_percent` |

## 5. Annotation process — Option B (independent multi-model)

Runs on the **17 new docs** (current 5 keep their v3-verified GT). Per doc:
1. Each of **5 frontier models** — Opus 5 · GPT-5.6 Sol · Grok 4.5 · Kimi K3 · Qwen3.8-Max
   (slugs in `sprints/v5/PRD.md`) — drafts the ground truth **independently**, following the
   rules above.
2. **Reconcile per field:** unanimous → auto-accept · majority (3-of-5) → accept (flag) ·
   split → **human adjudicates** against the source.
3. Record **inter-annotator agreement** (how often all 5 agreed) in §7 — an honest reliability
   signal for the dataset.

## 6. Composition *(filled in during Tasks 3–10)*

| Doc | Source | Technology | Geography | Split |
|---|---|---|---|---|
| _(to be filled)_ | | | | |

## 7. Splits & limitations

- **dev (10):** current 5 + 5 new — usable for prompt / few-shot iteration.
- **test (12, held-out):** new; **quarantined** from prompt iteration. Few-shot examples may
  come only from dev.
- **Limitations:** N=22 is modest; ground truth is model-drafted + human-adjudicated (not fully
  hand-built) — inter-annotator agreement is reported as the honesty signal; many hard fields
  are legitimately `not_found` in most docs.
- **Inter-annotator agreement:** _(recorded after Task 6)_
