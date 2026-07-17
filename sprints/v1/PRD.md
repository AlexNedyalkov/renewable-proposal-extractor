# Sprint v1 — PRD

## 1. Sprint Overview
Build the backend core of the AI-Powered Document Analyzer: a FastAPI service that accepts a renewable-energy project proposal PDF, extracts its text, runs a Claude-based structured extraction, and returns validated, schema-conformant financial/technical data — even when the source document has missing or unclear information. No frontend in this sprint; the API is the deliverable, exercised via manual requests (curl/Postman) and a real sample PDF.

## 2. Goals
- A running FastAPI service accepts a PDF upload and returns structured JSON extraction results.
- PDF text is reliably extracted from multi-page documents using pdfplumber.
- The Claude-based extraction step returns data conforming to a strict Pydantic schema, with explicit handling for missing/uncertain fields (no silent nulls, no crashes).
- Malformed, oversized, or non-PDF uploads return clear structured error responses instead of unhandled exceptions.
- The API contract (request/response shapes) is stable enough for the v2 frontend sprint to build against without backend changes.

## 3. User Stories
- As an analyst, I want to submit a project proposal PDF to an API, so that I can receive structured financial/technical data without manually reading the document.
- As an analyst, I want the extraction to explicitly flag missing or low-confidence fields, so that I know which data points still need manual verification.
- As a developer, I want a well-defined Pydantic schema for the extraction output, so that downstream consumers (the v2 frontend) get a stable, typed contract.
- As an analyst, I want to retrieve a previously submitted analysis by ID, so that I don't need to re-upload a file to view results again in the same session.

## 4. Technical Architecture

**Stack**: Python 3.11+, FastAPI, Pydantic, pdfplumber, Anthropic API (Claude), in-memory storage (no DB in v1).

**Extraction schema** — every extracted field is wrapped so missing/uncertain data is explicit, not a bare `null`:
```
ExtractedField:
  value: Any | None
  confidence: "high" | "medium" | "low" | "not_found"
  source_snippet: str | None   # short supporting quote from the document

ProposalExtraction:
  # Technical
  project_name, location, technology_type, installed_capacity_mw,
  expected_annual_generation_mwh, commercial_operation_date, developer_sponsor
  # Financial
  total_capex_usd, capex_per_mw, expected_irr_percent, payback_period_years,
  lcoe_usd_per_mwh, ppa_price_usd_per_mwh, ppa_term_years, debt_equity_ratio
  (each field is an ExtractedField)
```

**Component diagram**:
```
+-------------+     multipart/form-data      +---------------------------+
|   Client    |----------------------------->|       FastAPI App         |
| (curl/tests)|                              |   POST /api/documents     |
+-------------+<-----------------------------+---------------------------+
      ^                  JSON result                       |
      |                                                    v
      |                                      +---------------------------+
      |                                      |   PDF Text Extractor      |
      |                                      |   (pdfplumber)            |
      |                                      +---------------------------+
      |                                                    |
      |                                                    v
      |                                      +---------------------------+
      |                                      |   Extraction Service      |
      |                                      |   (Anthropic Claude API,  |
      |                                      |   structured JSON output) |
      |                                      +---------------------------+
      |                                                    |
      |                                                    v
      |                                      +---------------------------+
      |                                      |  Validator / Normalizer   |
      |                                      |  (Pydantic; missing/bad   |
      |                                      |  fields -> not_found)     |
      |                                      +---------------------------+
      |                                                    |
      |                                                    v
      |                                      +---------------------------+
      +--------------------------------------|  In-memory Result Store   |
         GET /api/documents/{id}              |  (dict: id -> result)     |
                                               +---------------------------+
```

**Data flow**: Client uploads PDF → endpoint validates file type/size → text extracted via pdfplumber → document text + schema sent to Claude with an extraction prompt requesting structured JSON → raw LLM JSON passed through the validator, which coerces anything missing/malformed to `confidence: "not_found"` rather than raising → result stored in-memory keyed by a generated `document_id` → JSON response returned to client. `GET /api/documents/{id}` re-serves a stored result.

## 5. Out of Scope
- Frontend UI (v2)
- Persistent database / storage beyond in-memory dict
- Authentication / multi-user support
- Batch or async/background job processing (all requests handled synchronously)
- Automated test suite and security scanning (v3, per skill rules — testing/security belong in later sprints)
- Deployment/production infrastructure
- Compiling the AI-assistant conversation log (final deliverable, addressed once implementation stabilizes)

## 6. Dependencies
- `ANTHROPIC_API_KEY` available as an environment variable
- Python 3.11+ installed
- Backend packages: `fastapi`, `uvicorn`, `pdfplumber`, `pydantic`, `anthropic`, `python-multipart`, `python-dotenv`
- At least one real sample project-proposal PDF (user-provided) for manual smoke testing in Task 9
