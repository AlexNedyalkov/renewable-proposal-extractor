# Sprint v3 — PRD

## 1. Sprint Overview
Sprint v3 addresses three concrete gaps surfaced by real-world testing in v1/v2 rather than adding new surface area: fixing the one schema field with no canonical format (`debt_equity_ratio`), building a repeatable way to measure extraction accuracy against known documents (tying back to the original 85%+ accuracy target), and closing the loop on the `GET /api/documents/{id}` endpoint that has existed unused since sprint v1 by giving analysts a way to look up a prior result.

## 2. Goals
- `debt_equity_ratio` (free-text, three inconsistent formats observed across real documents) is replaced with strictly-typed `debt_percent` and `equity_percent` numeric fields, across the schema, backend tests, API docs, and frontend e2e fixtures.
- A reusable, repeatable extraction-accuracy evaluation harness exists: ground-truthed against the 5 real sample PDFs from sprint v1, it reports a per-field and overall accuracy figure.
- Analysts can retrieve a previously analyzed document by ID from the UI, using the backend endpoint that already exists but nothing has called since sprint v1.

## 3. User Stories
- As an analyst, I want debt and equity reported as clean percentages rather than a free-text ratio, so that I can use them directly in calculations without manual parsing.
- As a developer/maintainer, I want a repeatable way to measure extraction accuracy against known documents, so that I can detect regressions or model-quality drift over time — directly answering the brief's question of how this system would be evaluated in production.
- As an analyst, I want to look up a document I already analyzed by its ID, so that I don't need to re-upload the same PDF to see its results again.

## 4. Technical Architecture

**Stack**: Unchanged from v1/v2 — FastAPI backend, Claude tool-use extraction, plain HTML/CSS/JS frontend, pytest + Playwright testing.

**New pieces**:
- `backend/tests/fixtures/ground_truth/*.json` — hand-verified expected values for each real sample PDF, derived from sprint v1's Task 10 manual review (already-observed-correct extractions, now formalized as fixtures).
- `backend/scripts/evaluate_extraction_accuracy.py` — a standalone script (not part of the API or default test suite) that runs the real pipeline against each real sample PDF, diffs the result against ground truth, and reports accuracy. Costs money (real API calls) and is run manually, same category as the existing `pytest -m live` tests.
- Frontend gains a second entry point into results rendering: "look up by ID" alongside "upload a new PDF", both funneling into the same `renderResults()`.

**Component diagram**:
```
                                          (existing, unchanged)
   Browser --upload PDF--> POST /api/documents --> extract/LLM/normalize/store
      |                                                      |
      | --lookup by id--> GET /api/documents/{id} -----------+
      |                                                      |
      +<----------------- {document_id, extraction} ---------+
                       (renders via the same renderResults())


   (offline, manual — not part of the running app)
   backend/scripts/evaluate_extraction_accuracy.py
      reads: backend/tests/fixtures/real_samples/*.pdf
             backend/tests/fixtures/ground_truth/*.json
      calls: extract_text() -> run_extraction() -> normalize_extraction()
             (the same pipeline functions POST /api/documents uses)
      writes: backend/tests/extraction_accuracy_report.md
```

**Data flow (lookup by ID)**: User enters a document ID and submits → `fetch GET /api/documents/{id}` → on 200, the exact same `renderResults()` used for fresh uploads renders the stored result → on 404, the existing error-banner pattern shows "No document found with that ID."

**Data flow (evaluation harness)**: Script iterates each real sample PDF → runs it through the same `extract_text`/`run_extraction`/`normalize_extraction` functions the API uses (no HTTP involved, direct function calls) → compares each field's extracted value against that document's ground-truth fixture → aggregates a per-field and overall match rate → writes a markdown report.

## 5. Out of Scope
- Full history/list view (would need a new `GET /api/documents` list endpoint) — still deferred; this sprint only adds single-ID lookup against the endpoint that already exists.
- Authentication.
- Moving off the in-memory store.
- Accessibility audit, retry/cancel UI affordances.
- README.md and the AI-assistant conversation log — still deferred by the user to the end of the project, not any specific sprint.

## 6. Dependencies
- Sprints v1 and v2 complete (backend + frontend both working).
- `ANTHROPIC_API_KEY` configured for the live-verification tasks in this sprint (schema fix re-check, evaluation harness run).
- The 5 real sample PDFs and their previously-observed-correct extractions from v1's Task 10 (`backend/tests/manual_smoke_test_notes.md`), used as the source for ground-truth fixtures.
