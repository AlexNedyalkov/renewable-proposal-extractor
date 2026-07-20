# Renewable Proposal Extractor

An AI-powered document analyzer for renewable energy investment proposals, built for TerraWatt Analytics: upload a project proposal PDF, get back structured technical and financial data — every field tagged with a confidence level and a verbatim source quote, so an analyst can see at a glance what's reliable and what still needs a manual check.

**Live in this repo:**
- A Python/FastAPI backend that extracts PDF text, runs it through Claude for structured extraction, validates/normalizes the result, and serves it over a JSON API.
- A plain HTML/CSS/JS frontend (served by the same backend, no separate server or CORS setup) for upload, results, and looking up a prior analysis by ID.
- pytest (backend) and Playwright (frontend/e2e) test suites, including opt-in tests that hit the real Anthropic API against both a controlled document and 5 real public project-financing PDFs.
- A ground-truth-based extraction accuracy evaluation harness (currently measuring **96.2%** field accuracy against the project's 85%+ target).

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env          # then edit .env and set ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

The app is now running at **http://127.0.0.1:8000** — the frontend is served automatically from the same process (upload a PDF, or look up a previous result by ID).

### 2. Running tests

```bash
cd backend
pytest                        # unit + integration tests, no network calls, no cost
pytest -m live                # opt-in: hits the real Anthropic API (7 tests, ~2 min, costs money)
```

```bash
cd e2e
npm install
npx playwright install chromium   # first time only
# with the backend running (see step 1):
npx playwright test                              # mocked E2E tests, no network calls
RUN_LIVE_TESTS=1 npx playwright test full-stack-smoke.spec.ts   # opt-in: real API, real document
```

### 3. Extraction accuracy evaluation (optional)

```bash
cd backend
python scripts/evaluate_extraction_accuracy.py    # costs money: 5 real Anthropic API calls
```

Runs the pipeline against 5 real public project-financing PDFs and scores the result against hand-verified ground truth. See `backend/tests/extraction_accuracy_report.md` for the last recorded run.

## Architecture

```
                    multipart/form-data                 GET /api/documents/{id}
   Browser --upload PDF-------------->  POST /api/documents  <--lookup by id-- Browser
      |                                        |                                  |
      |                                        v                                  |
      |                          extract -> Claude -> normalize -> store          |
      |                                        |                                  |
      +<----------- {document_id, extraction} -+----------------------------------+
                (renders the same way regardless of which path got there)
```

- **PDF text extraction**: `pdfplumber`, joined across all pages.
- **LLM extraction**: Claude, forced through tool-use so the response is always structured JSON. The tool's `input_schema` is generated directly from the Pydantic model (`ProposalExtraction.model_json_schema()`), so the schema and the LLM contract can't drift apart.
- **Validation/normalization**: every one of the 16 fields is validated independently — a single malformed or missing field falls back to `not_found` without discarding the other 15.
- **Storage**: in-memory dict, keyed by a generated `document_id` (see Known Limitations).

Full architecture diagrams and data flow are in each sprint's `WALKTHROUGH.md` (see [Project History](#project-history) below).

## Design Decisions & Trade-offs

- **Every field is confidence-tagged, not just present-or-null.** `{value, confidence, source_snippet}` for all 16 fields, always — `not_found` is explicit and never fabricated. Verified against 5 real institutional financing documents: the model consistently returned `not_found` rather than a plausible-looking guess for genuinely absent data, including one case where it correctly recognized a redacted line item and quoted "CONFIDENTIAL INFORMATION DELETED" as the source rather than inventing a number.
- **File-type validation checks the actual PDF magic bytes (`%PDF-`), not the client-supplied `Content-Type` header** — the header is trivially spoofable on an untrusted upload endpoint.
- **In-memory storage, not a database.** Fine for this prototype's scope; the trade-off is that results don't survive a server restart. `GET /api/documents/{id}` exists as a real endpoint so a future move to persistent storage wouldn't change the API contract.
- **Synchronous request handling, no job queue.** Simpler to build and reason about; the trade-off is a slow Claude call blocks the HTTP request for its duration (typically single-digit seconds).
- **`debt_equity_ratio` was replaced with typed `debt_percent`/`equity_percent`** after real-document testing found the original free-text field came back in 3 incompatible formats across documents. One document in the real test set actually contains *two different* debt/equity disclosures (a capital-structure percentage split and an unrelated leverage-ratio covenant metric) — exactly the ambiguity this fix targets. See `sprints/v3/`.
- **Extraction accuracy is measured against independently-verified ground truth**, not against the model's own prior outputs (which would be circular). Ground truth was built by re-reading each source PDF's extracted text directly, not by trusting earlier LLM runs.

## Testing Strategy

| Layer | Tool | What it covers | Cost |
| --- | --- | --- | --- |
| Backend unit | pytest | Schema validation, PDF extraction, LLM call construction/error handling, per-field normalization | Free |
| Backend integration | pytest + FastAPI `TestClient` | Both API endpoints, all documented error codes | Free |
| Backend live (opt-in) | `pytest -m live` | Real Anthropic API against 1 synthetic + 5 real documents | Real API calls |
| Frontend E2E (mocked) | Playwright | Upload flow, results rendering, validation, error states, lookup-by-id, responsive layout | Free |
| Frontend E2E live (opt-in) | Playwright, `RUN_LIVE_TESTS=1` | Real backend + real Anthropic API, driven entirely through the browser | Real API calls |
| Extraction accuracy | `scripts/evaluate_extraction_accuracy.py` | Field-level accuracy against hand-verified ground truth across 5 real documents | Real API calls |

Live/opt-in tests are deliberately excluded from default runs (`pytest -m live`, `RUN_LIVE_TESTS=1`) so routine test runs stay free, fast, and offline — the same pattern is used consistently across both the Python and Playwright suites.

## AI Assistants Used

This project was built with **Claude Code** (Anthropic) as the primary development assistant, across the full lifecycle: sprint planning, implementation via test-driven development, security scanning, and sprint documentation. Three custom slash-command skills structured the workflow:

- **`/prd`** — brainstormed and scoped each sprint's requirements into a `PRD.md` + atomic `TASKS.md`.
- **`/dev`** — implemented one task at a time: tests written first, then the minimum implementation to pass, then a security scan (`semgrep`, `pip-audit`, `npm audit`) before each commit.
- **`/walkthrough`** — generated a `WALKTHROUGH.md` per sprint documenting the architecture, every file produced, test coverage, and known limitations.

A log/export of the AI-assistant conversations used during development is at [`docs/ai-conversation-log.md`](docs/ai-conversation-log.md).

## Project History

Every sprint's planning, task breakdown, and post-hoc review is committed to the repo:

| Sprint | Focus | Docs |
| --- | --- | --- |
| v1 | Backend extraction pipeline | [`sprints/v1/PRD.md`](sprints/v1/PRD.md) · [`TASKS.md`](sprints/v1/TASKS.md) · [`WALKTHROUGH.md`](sprints/v1/WALKTHROUGH.md) |
| v2 | Frontend UI | [`sprints/v2/PRD.md`](sprints/v2/PRD.md) · [`TASKS.md`](sprints/v2/TASKS.md) · [`WALKTHROUGH.md`](sprints/v2/WALKTHROUGH.md) |
| v3 | Schema fix, accuracy evaluation, lookup-by-id | [`sprints/v3/PRD.md`](sprints/v3/PRD.md) · [`TASKS.md`](sprints/v3/TASKS.md) · [`WALKTHROUGH.md`](sprints/v3/WALKTHROUGH.md) |

Other reference docs:
- [`API_CONTRACT.md`](API_CONTRACT.md) — every endpoint, error code, and example payload, captured from the running app.
- [`backend/tests/manual_smoke_test_notes.md`](backend/tests/manual_smoke_test_notes.md) — results and analysis from running the pipeline against 5 real public project-financing documents.
- [`backend/tests/extraction_accuracy_report.md`](backend/tests/extraction_accuracy_report.md) — the extraction accuracy evaluation run and its caveats.
- [`project-plan-and-metrics.md`](project-plan-and-metrics.md) — the original project plan and target metrics this build was measured against.

## Known Limitations

- In-memory storage only — results don't survive a server restart.
- No authentication.
- Synchronous processing — no background job queue.
- Single-document lookup only, no history/list view (would need a new `GET /api/documents` list endpoint).
- `normalize_extraction()` doesn't yet reject a `null` value paired with a non-`not_found` confidence (observed once in evaluation; not systematic — see `extraction_accuracy_report.md`).
- The accuracy evaluation set is 5 documents — encouraging, not statistically robust.
- No accessibility audit performed.
- Not tested against documents long enough to approach Claude's context window limits.
