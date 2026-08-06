# Sprint v4 — Tasks (Prompt-engineering improvements)

Goal: improve extraction **quality** through prompt engineering — clearer prompt
structure and precise, disambiguated field definitions — and measure the impact
against the accuracy eval. Each task is one committed improvement.

- [x] **Task 1 — Restructure the extraction prompt into XML-delimited sections** (P0)
    Acceptance: `_build_prompt` uses explicit `<role>` / `<task>` / `<instructions>`
    / `<document>` tags (Claude follows XML delimiters more reliably than prose, and
    a clear `<document>` boundary starts to harden the user-content/instruction split).
    Tests still pass.
    Files: `backend/app/llm_extraction.py`
    Done 2026-07-29 — XML-tagged sections; extraction tests green.

- [x] **Task 2 — Add precise per-field definitions to the extraction schema** (P0)
    Acceptance: every one of the 16 fields carries a `Field(description=...)` giving
    definition + unit + disambiguation — especially the ambiguous financial metrics
    (IRR vs return-on-equity; debt%/equity% vs a leverage ratio; LCOE cost vs PPA
    price). Descriptions flow into the tool `input_schema` (verified via
    `model_json_schema()`). Full suite passes (40).
    Files: `backend/app/schemas.py`
    Done 2026-07-29 — 16/16 fields described; schema verified; 40 tests green.

- [x] **Task 3 — Pin `temperature=0` for deterministic extraction** (P0, do before the eval)
    Acceptance: `run_extraction` passes `temperature=0` to the Claude call. Extraction
    is a temp=0 use case (we want the single most-likely reading of each value, not
    sampling). Also a *precondition for trustworthy eval* — at the default temp the
    model can give different answers on re-run, so before/after deltas would include
    sampling noise. Tests pass.
    Files: `backend/app/llm_extraction.py`
    Done 2026-08-05 — `temperature=0` set; asserted by a new test. 41 tests green.
    SUPERSEDED 2026-08-06 (Task 6): the live eval hit a 400 — `claude-sonnet-5`
    deprecated `temperature`. Removed the param; determinism verified empirically.

- [x] **Task 4 — Move role + instructions into a dedicated `system` message** (P0, do before the eval)
    Acceptance: `run_extraction` passes a `system=` argument carrying the `<role>` and
    `<instructions>` content, leaving the user turn to carry the `<document>` (untrusted
    content). Claude weights the system message most strongly, so behavioral rules
    belong there — and it cleanly separates our instructions from the document text,
    which also helps the Week-6 prompt-injection story. Surfaced by the Lesson 01
    concepts ledger (we weren't using a system message at all). Tests pass.
    Files: `backend/app/llm_extraction.py`
    Done 2026-08-05 — `_SYSTEM_PROMPT` (role+instructions) via `system=`; document in
    the user turn via `_build_user_content`. New test asserts the document stays out of
    the system prompt. 41 tests green.

- [x] **Task 5 — Few-shot examples + Chain-of-Thought for ambiguous fields** (P0)
    Approach = A + D (few-shot CoT adapted to forced tool-use):
      A. a `reasoning` field declared *first* in the tool schema, so the model does
         chain-of-thought inside the forced tool call (temp=0, one call); logged at
         INFO for observability, then discarded (callers still get the 16-field dict).
      D. few-shot worked examples in the system prompt demonstrating the reasoning
         for the ambiguous metrics (IRR vs return-on-equity, debt% vs leverage ratio).
    [x] A — `_ReasonedExtraction` wrapper + INFO logging + tests (2026-08-05).
    [x] D — 5 worked examples in the system prompt (3 confident : 2 not_found, to
        match the real distribution and avoid anchoring on not_found) + test (2026-08-05).

- [x] **Task 6 — Measure the prompt/schema changes against the eval** (P0)
    Acceptance: run the accuracy eval on the improved pipeline; record the field-level
    before/after. Done 2026-08-06 — 96.2% → 97.5% (77→78/80): fixed 3 (IRR, debt%,
    equity%), broke 2 (`capex_per_mw`, a derived metric — motivates Task 7). Ran twice
    → identical (reproducible even after removing the deprecated `temperature`). Also
    fixed `evaluate_extraction_accuracy.py` to load `.env`. Full write-up in
    `backend/tests/extraction_accuracy_report.md` (Sprint v4 Re-run).
    Files: `backend/scripts/evaluate_extraction_accuracy.py`, report.

- [~] **Task 7 — Extract faithfully, derive in code** (P2)
    [x] `capex_per_mw = total_capex_usd / installed_capacity_mw` — new
        `app/derivation.py`, wired into the route + eval, 5 tests. Provenance in
        `source_snippet` (incl. both input snippets); confidence = weaker input; only
        fires when capex is not_found + inputs are valid numbers + capacity > 0. Fixed
        cambodia + triconboston capex (2026-08-06). Caveat: derivation cascades upstream
        input errors — see report.
    [ ] Interchangeable debt/equity forms (%, ratio, multiple) — STILL DEFERRED; the
        eval hasn't demanded it (debt/equity pass). Watch the 100%-sum trap (3+ sources).
