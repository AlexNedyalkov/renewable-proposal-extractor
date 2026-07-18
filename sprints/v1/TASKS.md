# Sprint v1 — Tasks

- [x] Task 1: Project setup — FastAPI scaffold, deps, env config (P0)
    Acceptance: FastAPI app boots with `uvicorn app.main:app --reload` and returns 200 on `GET /health`; `requirements.txt` lists fastapi, uvicorn, pdfplumber, pydantic, anthropic, python-multipart, python-dotenv; `.env.example` documents `ANTHROPIC_API_KEY`; `.gitignore` excludes venv/`.env`/`__pycache__`.
    Files: backend/app/main.py, backend/requirements.txt, backend/.env.example, .gitignore
    Completed: 2026-07-17 — Verified via pytest + a live uvicorn boot. pip-audit found 19 known CVEs in initially-pinned versions (fastapi/starlette, python-multipart, python-dotenv, pytest, pdfminer-six); bumped all to patched releases and re-verified clean.

- [x] Task 2: Define extraction schema (P0)
    Acceptance: Pydantic models in `schemas.py` define `ExtractedField` (value, confidence, source_snippet) and `ProposalExtraction` (technical + financial fields per PRD §4); a hand-built sample dict validates successfully against the model.
    Files: backend/app/schemas.py
    Completed: 2026-07-18 — 5 unit tests (valid/invalid confidence, optional value/snippet, full sample dict, missing-field rejection). pip-audit and semgrep both clean, no new dependencies.

- [x] Task 3: PDF text extraction module (P0)
    Acceptance: `extract_text(pdf_path) -> str` extracts and joins text across all pages of a multi-page PDF using pdfplumber; raises a clear, typed exception when a PDF has no extractable text (e.g. scanned image with no OCR).
    Files: backend/app/pdf_extraction.py
    Completed: 2026-07-18 — 2 unit tests against fpdf2-generated fixtures (multi-page text PDF, blank no-text PDF). Added fpdf2 as a test-only dependency to generate fixtures. pip-audit and semgrep both clean.

- [x] Task 4: Extraction prompt + Claude client wrapper (P0)
    Acceptance: `run_extraction(document_text: str) -> dict` sends the document text and target schema to Claude via the Anthropic API using structured/tool-use output, and returns a parsed JSON dict shaped like `ProposalExtraction`; testable with a mocked Anthropic client (no live API call required to verify the function's control flow).
    Files: backend/app/llm_extraction.py
    Completed: 2026-07-18 — Uses Claude tool-use forced via tool_choice, with input_schema generated directly from ProposalExtraction.model_json_schema() (single source of truth). 3 unit tests against a fake Anthropic client (no live API calls). pip-audit and semgrep both clean, no new dependencies. Not yet exercised against the real Anthropic API — that starts with Task 5's live smoke test.

- [x] Task 5: Live smoke test of Claude extraction against the real Anthropic API (P1)
    Acceptance: A `pytest.mark.live`-marked test calls `run_extraction()` with no mock client, using the real `ANTHROPIC_API_KEY` from `.env`, against a short hand-written proposal paragraph with an unambiguous project name and financial figure. Asserts the result validates against `ProposalExtraction` and that `project_name` (and at least one financial field) come back with confidence other than `not_found`. The `live` marker is excluded from the default `pytest` run (via `pytest.ini`) so routine test runs stay free, fast, and offline; it only runs when explicitly requested with `pytest -m live`.
    Files: backend/pytest.ini, backend/tests/test_llm_extraction_live.py
    Completed: 2026-07-18 — Confirmed default `pytest` run deselects the live test (0 cost/network). Ran explicitly with `pytest -m live` against the real Anthropic API using the user's key: passed in ~9s, correctly extracted project_name ("Sunridge Solar Farm") and total_capex_usd with non-"not_found" confidence. pip-audit and semgrep both clean.

- [x] Task 6: Validation & normalization layer (P0)
    Acceptance: `normalize_extraction(raw_dict) -> ProposalExtraction` validates raw LLM JSON against the Pydantic schema; any missing, malformed, or unparseable field is coerced to `confidence="not_found"`/`value=None` rather than raising, and the function always returns a valid `ProposalExtraction` instance.
    Files: backend/app/validation.py
    Completed: 2026-07-18 — Per-field normalization: each of the 15 fields is validated independently, so one bad/missing field falls back to not_found without discarding valid fields elsewhere in the same response. 6 unit tests (fully valid, missing fields, invalid confidence, wrong-shaped field, empty dict, None input). pip-audit and semgrep both clean, no new dependencies.

- [ ] Task 7: POST /api/documents endpoint (P0)
    Acceptance: Endpoint accepts a multipart PDF upload; rejects non-PDF files and files over a defined size limit with a 400 + structured error body; on valid input, runs extract → LLM → normalize synchronously, stores the result in an in-memory dict keyed by a generated `document_id`, and returns `{document_id, extraction}` as JSON.
    Files: backend/app/main.py, backend/app/routes/documents.py, backend/app/store.py

- [ ] Task 8: GET /api/documents/{id} endpoint (P0)
    Acceptance: Returns the stored extraction JSON for a known `document_id`; returns 404 with a structured error body for an unknown id.
    Files: backend/app/routes/documents.py

- [ ] Task 9: Error handling for extraction failures (P1)
    Acceptance: If PDF text extraction fails or the Claude API call errors/times out, the endpoint returns a structured 500/502 error payload (error code + message) instead of an unhandled traceback; verified with a forced-failure case (corrupt PDF fixture or invalid API key).
    Files: backend/app/routes/documents.py, backend/app/llm_extraction.py

- [ ] Task 10: Manual smoke test against a real sample PDF (P1)
    Acceptance: Using a sample PDF provided by the user, `POST /api/documents` returns a populated `ProposalExtraction` with at least `project_name` and one financial field correctly identified; outcome recorded in a short notes file.
    Files: backend/tests/manual_smoke_test_notes.md

- [ ] Task 11: API contract documentation (P1)
    Acceptance: Actual implemented request/response JSON shapes are captured in `API_CONTRACT.md` at the repo root (endpoints, example requests/responses); any drift from PRD §4 is called out and reconciled.
    Files: API_CONTRACT.md
