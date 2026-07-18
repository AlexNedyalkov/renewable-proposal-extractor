# Sprint v1 — Walkthrough

## Summary

Sprint v1 built the entire backend of the AI-Powered Document Analyzer: a
FastAPI service that accepts a renewable-energy project proposal PDF,
extracts its text, sends it to Claude for structured extraction, validates
and normalizes the result, and serves it back over a JSON API. It was
validated against both a controlled synthetic document and 5 real public
project-financing filings, and every stage degrades gracefully (structured
errors, `not_found` fields) instead of crashing or hallucinating. No
frontend yet — that's v2.

## Architecture Overview

```
                    multipart/form-data
   Client  ------------------------------------->  FastAPI App
  (curl/tests/                                     POST /api/documents
   future UI)  <-------------------------------    GET  /api/documents/{id}
                     JSON result / error                 |
                                                          v
                                          +---------------------------+
                                          |  PDF Text Extractor       |
                                          |  (pdfplumber)             |
                                          |  raises NoExtractableText |
                                          |  Error on empty/scanned   |
                                          +---------------------------+
                                                          |
                                                          v
                                          +---------------------------+
                                          |  Claude Extraction        |
                                          |  (Anthropic tool-use,     |
                                          |  schema = ProposalExtrac- |
                                          |  tion.model_json_schema())|
                                          |  raises ExtractionError   |
                                          |  on any API failure       |
                                          +---------------------------+
                                                          |
                                                          v
                                          +---------------------------+
                                          |  Validator / Normalizer   |
                                          |  (per-field validation;   |
                                          |  bad/missing -> not_found,|
                                          |  never raises)            |
                                          +---------------------------+
                                                          |
                                                          v
                                          +---------------------------+
                                          |  In-memory Store          |
                                          |  (dict: document_id ->    |
                                          |  ProposalExtraction)      |
                                          +---------------------------+
```

Every arrow going "down" can fail; every failure is caught at the route
level and converted into one of six structured error responses (see
`API_CONTRACT.md`) rather than an unhandled traceback.

## Files Created/Modified

### backend/app/schemas.py
**Purpose**: Defines the extraction data contract — the single source of truth for what gets extracted and in what shape.
**Key Components**:
- `ExtractedField` — wraps every data point with a value, a confidence level, and a supporting quote
- `ProposalExtraction` — 15 named `ExtractedField`s (7 technical, 8 financial)

**How it works**:
Every extracted fact — not just the ones the LLM found, but every field the
schema defines — is wrapped in the same three-part shape:

```python
class ExtractedField(BaseModel):
    value: Optional[Any] = None
    confidence: Confidence  # "high" | "medium" | "low" | "not_found"
    source_snippet: Optional[str] = None
```

This was the key design decision of the whole sprint: rather than a bare
`null` for missing data (which is ambiguous — is it missing, or did we not
look?), every field always carries an explicit confidence and, when found,
a verbatim quote proving where the value came from. `ProposalExtraction`
is later fed straight into `model_json_schema()` (Task 4) to become the
Claude tool's input schema, so the schema is never hand-duplicated — one
Pydantic model drives validation, the LLM contract, and the API response.

### backend/app/pdf_extraction.py
**Purpose**: Turns an uploaded PDF file into plain text for the LLM to read.
**Key Functions**:
- `extract_text(pdf_path)` — joins text across all pages
- `NoExtractableTextError` — raised when a PDF has no extractable text

**How it works**:
```python
def extract_text(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        pages_text = [p.extract_text() for p in pdf.pages if p.extract_text()]
    text = "\n".join(pages_text).strip()
    if not text:
        raise NoExtractableTextError(...)
    return text
```
A scanned PDF (image-only, no text layer) will parse "successfully" as far
as pdfplumber is concerned but yield empty strings for every page — this
function is what turns that silent-empty-result into a typed exception the
route can catch and turn into a clear `400 no_extractable_text` instead of
silently sending an empty document to Claude.

### backend/app/llm_extraction.py
**Purpose**: Calls Claude to perform the actual extraction, using tool-use to force a structured response.
**Key Functions**:
- `run_extraction(document_text, client=None)` — the extraction call
- `ExtractionError` — raised for any client/API failure or malformed response

**How it works**:
```python
schema = ProposalExtraction.model_json_schema()
response = client.messages.create(
    model=MODEL,
    tools=[{"name": EXTRACTION_TOOL_NAME, "input_schema": schema, ...}],
    tool_choice={"type": "tool", "name": EXTRACTION_TOOL_NAME},
    messages=[{"role": "user", "content": _build_prompt(document_text)}],
)
```
`tool_choice` forces Claude to respond via the tool rather than free text,
so the response is always a JSON object shaped like the schema (barring
outright API failure). The `client` parameter defaults to a real
`anthropic.Anthropic()` but accepts an injected fake in tests, which is
what makes 4 of the unit tests possible without ever touching the network.
Any exception from the API call — auth failure, rate limit, timeout,
connection drop — is caught by a deliberately broad `except Exception` and
re-raised as `ExtractionError`, so nothing SDK-specific leaks past this
module's boundary.

### backend/app/validation.py
**Purpose**: Guarantees the LLM's raw JSON always becomes a valid `ProposalExtraction`, no matter how malformed the input.
**Key Functions**:
- `normalize_extraction(raw_dict)` — never raises
- `_normalize_field(raw_field)` — per-field fallback to `not_found`

**How it works**:
```python
normalized = {
    field_name: _normalize_field(raw_dict.get(field_name))
    for field_name in ProposalExtraction.model_fields
}
return ProposalExtraction(**normalized)
```
The key design choice: normalization happens **per field**, not for the
whole document at once. If Claude returns 14 good fields and one with an
invalid `confidence` value, only that one field falls back to `not_found`
— the other 14 are preserved. A naive `ProposalExtraction(**raw_dict)`
would instead reject the *entire* response for one bad field, which is
exactly the brittleness the brief asked us to avoid.

### backend/app/store.py
**Purpose**: In-memory persistence for submitted analyses.
**Key Functions**: `save_document(id, extraction)`, `get_document(id)`
**How it works**: A module-level `dict`. Deliberately not a database — v1's
PRD scoped persistence out, and an in-memory store is enough to prove the
submit/retrieve API contract works. It does **not** survive a server
restart; that's the main limitation to flag for v2/v3.

### backend/app/routes/documents.py
**Purpose**: Wires the whole pipeline together behind `POST /api/documents` and `GET /api/documents/{id}`.
**Key Components**: `DocumentAnalysisResponse`, `upload_document()`, `get_document_analysis()`

**How it works**:
```python
if not contents.startswith(b"%PDF-"):
    raise _error(400, "invalid_file_type", "Only PDF files are supported.")
```
File-type validation checks the actual PDF magic bytes, not the
client-supplied `Content-Type` header — headers are trivially spoofable, so
trusting one for a security-relevant decision on an untrusted upload
endpoint would be a real gap. From there, the route runs extract → LLM →
normalize synchronously and catches failures at each stage, mapping them to
the 6 documented error codes (see `API_CONTRACT.md`) instead of letting
exceptions propagate into a raw 500 traceback.

### backend/app/main.py
**Purpose**: FastAPI application entrypoint.
**How it works**: Creates the `FastAPI` app, includes the documents router,
and exposes `GET /health` for liveness checks. Deliberately minimal.

### backend/requirements.txt / backend/.env.example / backend/pytest.ini
**Purpose**: Environment and tooling configuration.
**How it works**: `requirements.txt` pins runtime deps (fastapi, pdfplumber,
anthropic, etc.) plus test-only deps (pytest, httpx, fpdf2 for generating
PDF fixtures). Every pinned version was checked with `pip-audit`; several
were bumped mid-sprint after the initial pins turned out to have known
CVEs. `pytest.ini` registers a custom `live` marker and excludes it by
default (`addopts = -m "not live"`), so tests that call the real Anthropic
API only run when explicitly requested with `pytest -m live` — keeping
routine test runs free, fast, and offline.

### API_CONTRACT.md
**Purpose**: Documents the actual implemented API, including every error
code, generated from real captured responses rather than written from
memory. Also reconciles 4 details the PRD left unspecified (file size
limit, magic-byte validation, concrete error code names, `/health`).

### Tests
- `tests/test_schemas.py` (5 unit) — `ExtractedField`/`ProposalExtraction` validation, confidence enum enforcement
- `tests/test_pdf_extraction.py` (2 unit) — multi-page join, no-text-PDF exception, using fpdf2-generated fixtures
- `tests/test_llm_extraction.py` (4 unit) — tool-use call shape, missing-tool-use error, client-error wrapping, all against a fake Anthropic client
- `tests/test_validation.py` (6 unit) — per-field fallback behavior across valid/missing/malformed/empty/`None` input
- `tests/test_health.py` (1 integration) — liveness check
- `tests/test_documents_endpoint.py` (8 integration) — upload happy path, spoofed content-type rejection, oversized file, no-extractable-text, GET known/unknown id, PDF-crash → 500, extraction-failure → 502
- `tests/test_llm_extraction_live.py` (1, opt-in) — real Anthropic API call
- `tests/test_documents_endpoint_live.py` (6, opt-in) — full pipeline against a synthetic proposal plus 5 real ADB project-financing PDFs
- `tests/conftest.py` — shared PDF fixtures (multi-page text, blank/no-text)
- `tests/manual_smoke_test_notes.md` — human-readable write-up of the real-document extraction results

## Data Flow

1. Client `POST`s a PDF as `multipart/form-data` to `/api/documents`.
2. The route reads the bytes, checks the `%PDF-` signature and 20MB size cap.
3. Bytes are written to a temp file; `extract_text()` pulls text via pdfplumber; the temp file is always cleaned up (`finally`).
4. The document text is sent to Claude via `run_extraction()`, forced through tool-use so the response is structured JSON.
5. `normalize_extraction()` validates the raw JSON field-by-field against `ProposalExtraction`, coercing anything bad to `not_found` rather than raising.
6. The result is stored in-memory under a generated `document_id` and returned as `{document_id, extraction}`.
7. `GET /api/documents/{id}` re-serves the same shape from the store, or a structured 404.

## Test Coverage

- **Unit**: 17 tests — schema validation, PDF text extraction, Claude tool-use call construction and error wrapping, per-field normalization fallback logic.
- **Integration**: 9 tests — both endpoints via FastAPI's `TestClient`, covering the happy path and every documented error response.
- **Live (opt-in, real API)**: 7 tests — excluded from default runs (`pytest -m live` required); one hand-written document, one synthetic multi-field proposal, and 5 real public project-financing PDFs, run through the full pipeline with zero mocking.
- **Total**: 26 tests run by default `pytest`; 33 including opt-in live tests.

## Security Measures

- **File-type validation by content, not header**: checks the actual `%PDF-` magic bytes rather than the spoofable `Content-Type` header.
- **File size cap**: 20MB, enforced before any parsing happens.
- **No leaked internals**: both PDF-parsing crashes and Claude API failures are caught and returned as structured `{error, message}` bodies, never a raw traceback.
- **Dependency scanning**: every dependency change in the sprint was checked with `pip-audit`; the initial Task 1 pins had 19 known CVEs across 5 packages (fastapi/starlette, python-multipart, python-dotenv, pytest, pdfminer-six), all bumped to patched versions before merging.
- **Static analysis**: `semgrep --config auto` run and clean after every task.
- **Secrets**: `ANTHROPIC_API_KEY` lives only in `backend/.env` (gitignored); `.env.example` documents the variable name without a value.

## Known Limitations

- **In-memory store only** — results don't survive a server restart; no database.
- **No authentication** — anyone who can reach the API can submit/retrieve documents.
- **Synchronous processing** — a slow Claude call blocks the request; no background job queue.
- **`debt_equity_ratio` has no canonical format** — real documents produced three different representations (`"75:25"`, a currency pair, `"2.94x/2.24x"`) since the field is a loosely-typed string. A production version should likely split compound fields like this into strictly-typed numeric sub-fields.
- **Financial fields often come back `not_found` on real institutional documents** — not a bug (the model correctly avoids hallucinating), but it means real-world usefulness depends heavily on how explicitly a given proposal states its financials. See `manual_smoke_test_notes.md` for the full breakdown.
- **No frontend yet** — the API has no consumer besides tests and curl.
- **No handling for documents that exceed Claude's context window** — untested; large multi-hundred-page proposals mentioned in the brief haven't been tried.

## What's Next

Per the PRD's sprint sequencing:
- **v2**: a basic web frontend (upload PDF, view extracted results, loading/error states) consuming this API.
- **v3**: broader reliability/quality work — could include splitting compound fields like `debt_equity_ratio`, testing against a real TerraWatt proposal document, handling large documents relative to Claude's context window, and revisiting whether persistence needs to move beyond in-memory storage.
