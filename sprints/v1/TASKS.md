# Sprint v1 — Tasks

- [ ] Task 1: Project setup — FastAPI scaffold, deps, env config (P0)
    Acceptance: FastAPI app boots with `uvicorn app.main:app --reload` and returns 200 on `GET /health`; `requirements.txt` lists fastapi, uvicorn, pdfplumber, pydantic, anthropic, python-multipart, python-dotenv; `.env.example` documents `ANTHROPIC_API_KEY`; `.gitignore` excludes venv/`.env`/`__pycache__`.
    Files: backend/app/main.py, backend/requirements.txt, backend/.env.example, .gitignore

- [ ] Task 2: Define extraction schema (P0)
    Acceptance: Pydantic models in `schemas.py` define `ExtractedField` (value, confidence, source_snippet) and `ProposalExtraction` (technical + financial fields per PRD §4); a hand-built sample dict validates successfully against the model.
    Files: backend/app/schemas.py

- [ ] Task 3: PDF text extraction module (P0)
    Acceptance: `extract_text(pdf_path) -> str` extracts and joins text across all pages of a multi-page PDF using pdfplumber; raises a clear, typed exception when a PDF has no extractable text (e.g. scanned image with no OCR).
    Files: backend/app/pdf_extraction.py

- [ ] Task 4: Extraction prompt + Claude client wrapper (P0)
    Acceptance: `run_extraction(document_text: str) -> dict` sends the document text and target schema to Claude via the Anthropic API using structured/tool-use output, and returns a parsed JSON dict shaped like `ProposalExtraction`; testable with a mocked Anthropic client (no live API call required to verify the function's control flow).
    Files: backend/app/llm_extraction.py

- [ ] Task 5: Validation & normalization layer (P0)
    Acceptance: `normalize_extraction(raw_dict) -> ProposalExtraction` validates raw LLM JSON against the Pydantic schema; any missing, malformed, or unparseable field is coerced to `confidence="not_found"`/`value=None` rather than raising, and the function always returns a valid `ProposalExtraction` instance.
    Files: backend/app/validation.py

- [ ] Task 6: POST /api/documents endpoint (P0)
    Acceptance: Endpoint accepts a multipart PDF upload; rejects non-PDF files and files over a defined size limit with a 400 + structured error body; on valid input, runs extract → LLM → normalize synchronously, stores the result in an in-memory dict keyed by a generated `document_id`, and returns `{document_id, extraction}` as JSON.
    Files: backend/app/main.py, backend/app/routes/documents.py, backend/app/store.py

- [ ] Task 7: GET /api/documents/{id} endpoint (P0)
    Acceptance: Returns the stored extraction JSON for a known `document_id`; returns 404 with a structured error body for an unknown id.
    Files: backend/app/routes/documents.py

- [ ] Task 8: Error handling for extraction failures (P1)
    Acceptance: If PDF text extraction fails or the Claude API call errors/times out, the endpoint returns a structured 500/502 error payload (error code + message) instead of an unhandled traceback; verified with a forced-failure case (corrupt PDF fixture or invalid API key).
    Files: backend/app/routes/documents.py, backend/app/llm_extraction.py

- [ ] Task 9: Manual smoke test against a real sample PDF (P1)
    Acceptance: Using a sample PDF provided by the user, `POST /api/documents` returns a populated `ProposalExtraction` with at least `project_name` and one financial field correctly identified; outcome recorded in a short notes file.
    Files: backend/tests/manual_smoke_test_notes.md

- [ ] Task 10: API contract documentation (P1)
    Acceptance: Actual implemented request/response JSON shapes are captured in `API_CONTRACT.md` at the repo root (endpoints, example requests/responses); any drift from PRD §4 is called out and reconciled.
    Files: API_CONTRACT.md
