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

- [ ] **Task 3 — Few-shot examples + Chain-of-Thought for ambiguous fields** (P0)
    Acceptance: the prompt guides the model to reason about which metric is which
    before filling ambiguous fields (CoT), and/or shows a few worked examples for the
    tricky cases.

- [ ] **Task 4 — Measure the prompt/schema changes against the eval** (P0)
    Acceptance: run the accuracy eval on the original prompt vs the improved one;
    record whether accuracy on the ambiguous fields moved. Before/after numbers.
    Files: `backend/scripts/evaluate_extraction_accuracy.py`

- [ ] **Task 5 (deferred) — Interchangeable financial metrics: extract faithfully,
    derive in code** (P2)
    Idea: the LLM extracts whichever *form* a metric is stated in (%, ratio, multiple)
    plus a form label; deterministic code converts to canonical debt%/equity%. Keeps
    arithmetic out of the LLM (removes a hallucination class) and preserves provenance.
    Watch the 100%-sum trap with 3+ funding sources. Deferred — validate against the
    eval before building.
