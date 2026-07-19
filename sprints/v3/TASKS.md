# Sprint v3 — Tasks

- [x] Task 1: Replace debt_equity_ratio with debt_percent/equity_percent in the schema and backend tests (P0)
    Acceptance: `backend/app/schemas.py` no longer has `debt_equity_ratio`; it has `debt_percent` and `equity_percent` (both `ExtractedField`, numeric values expected), bringing the schema to 16 total fields. Every backend test referencing the old 15-field shape (`test_schemas.py`, `test_validation.py`, `test_llm_extraction.py`, `test_documents_endpoint.py`) is updated to the new shape and passes.
    Files: backend/app/schemas.py, backend/tests/test_schemas.py, backend/tests/test_validation.py, backend/tests/test_llm_extraction.py, backend/tests/test_documents_endpoint.py
    Completed: 2026-07-19 — Confirmed red first: updating test fixtures to use debt_percent/equity_percent before touching the schema correctly failed 2 of 4 affected test files (the ones that instantiate ProposalExtraction directly); the other 2 passed trivially because normalize_extraction()'s per-field fallback already absorbed the mismatch by itself — a nice confirmation that Task 6 (v1)'s robustness design works as intended, though it also means those tests alone wouldn't have caught this gap. No hardcoded references to the old field name existed elsewhere in app/ (checked via grep). model_json_schema() confirmed to auto-reflect the new 16-field list, so the Claude tool schema updates with zero extra code. Full backend suite (28 tests) passes. Security: semgrep clean, pip-audit clean, no new dependencies.

- [ ] Task 2: Update API_CONTRACT.md and frontend e2e fixtures for the new schema (P0)
    Acceptance: `API_CONTRACT.md`'s field list and example payloads show `debt_percent`/`equity_percent` (16 fields, not 15). `e2e/tests/results-view.spec.ts` and `e2e/tests/responsive-empty-state.spec.ts` canned responses are updated to match. Full e2e suite passes.
    Files: API_CONTRACT.md, e2e/tests/results-view.spec.ts, e2e/tests/responsive-empty-state.spec.ts

- [ ] Task 3: Ground-truth fixtures for the 5 real sample PDFs (P0)
    Acceptance: A JSON fixture per real sample PDF under `backend/tests/fixtures/ground_truth/` records the manually-verified correct value for every field sprint v1's Task 10 already confirmed extracts correctly (reusing the observed results documented in `manual_smoke_test_notes.md`), with fields genuinely absent from the source document marked `not_found`. Field names match the Task 1 schema (`debt_percent`/`equity_percent`, not the old field).
    Files: backend/tests/fixtures/ground_truth/*.json

- [ ] Task 4: Extraction accuracy evaluation script (P0)
    Acceptance: `backend/scripts/evaluate_extraction_accuracy.py` runs the real pipeline (`extract_text` → `run_extraction` → `normalize_extraction`, real Anthropic API call) against each real sample PDF, compares each field's extracted value/confidence against its ground-truth fixture, and computes a per-field and overall match rate. Not part of the default test suite (costs money); run manually with `python scripts/evaluate_extraction_accuracy.py`.
    Files: backend/scripts/evaluate_extraction_accuracy.py

- [ ] Task 5: "Look up previous analysis" UI (P0)
    Acceptance: Frontend has a small form (ID input + button) that calls `GET /api/documents/{id}`; on success it renders using the same `renderResults()` as a fresh upload; on 404 it shows a clear "no document found" message via the existing error-banner pattern. Playwright test covers both the found and not-found cases, each with a screenshot.
    Files: frontend/index.html, frontend/app.js, frontend/styles.css, e2e/tests/lookup-by-id.spec.ts, e2e/tests/screenshots/

- [ ] Task 6: Re-verify the schema fix against the real API (P1)
    Acceptance: Re-run `pytest -m live` and confirm the real Anthropic API populates `debt_percent`/`equity_percent` correctly for at least one real sample PDF that previously had a `debt_equity_ratio` value (e.g. `triconboston_wind.pdf`, previously "75:25"). Outcome documented.
    Files: backend/tests/manual_smoke_test_notes.md

- [ ] Task 7: Run the evaluation harness and document results (P1)
    Acceptance: The Task 4 script is actually run once against all 5 real samples (with the fixed schema). Results (overall accuracy %, per-field breakdown, notable misses) are written to a report and explicitly compared against `project-plan-and-metrics.md`'s 85%+ accuracy target — call out whether it's met and why.
    Files: backend/tests/extraction_accuracy_report.md

- [ ] Task 8: Verify lookup-by-id against a real stored document (P1)
    Acceptance: Upload a real sample PDF live, copy its returned `document_id`, and use the Task 5 UI to retrieve it — confirm the same data renders as the original upload. Outcome documented.
    Files: e2e/tests/lookup-by-id.spec.ts (extended) or a short notes addition
