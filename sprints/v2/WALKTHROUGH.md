# Sprint v2 — Walkthrough

## Summary

Sprint v2 built the frontend: a plain HTML/CSS/JS single page, served directly by the existing FastAPI backend (no separate server, no CORS needed), that lets an analyst upload a proposal PDF and see every extracted field — including confidence and source snippet — without leaving the page. It handles the full state machine (empty → loading → results or error) and was verified against the real backend and a real document, not just mocks. Along the way it also fixed a real production bug in the backend: the app never actually loaded `.env`.

## Architecture Overview

```
                         GET /, /styles.css, /app.js
   Browser  <-------------------------------------------  FastAPI StaticFiles
  (index.html                                              mount (serves frontend/)
   + app.js)  ------------------------------------------>
                    fetch POST /api/documents (FormData)
                              |
                              v
              +----------------------------------------+
              |   Existing backend pipeline (v1)        |
              |   extract -> Claude -> normalize -> store|
              +----------------------------------------+
                              |
                    JSON: {document_id, extraction}
                     or {detail: {error, message}}
                              |
                              v
   Browser renders one of:
     - results (15 fields: value, confidence badge, snippet)
     - error banner (detail.message)
     - inline validation message (no request ever sent)
```

Frontend state machine, all driven by a single form submit handler in `app.js`:

```
        [empty-state visible]
                |  submit (no file / non-PDF)
                |----------------> [validation-error shown, no fetch]
                |  submit (valid PDF)
                v
        [empty-state hidden, loading visible]
                |
       fetch resolves
                |
        +-------+--------+
        |                |
    response.ok      !response.ok
        |                |
        v                v
  [results shown]   [error-banner shown]
```

## Files Created/Modified

### frontend/index.html
**Purpose**: The single page shell — structure for the upload form, and containers for every UI state (validation error, error banner, loading, empty state, results).
**Key Components**: `#upload-form` (file input + submit button), `#validation-error`, `#error-banner`, `#loading`, `#empty-state`, `#results` — every stateful element `hidden` by default except `#empty-state`.

**How it works**:
Every dynamic region of the page exists as a real element in the HTML from the start, toggled via the `hidden` attribute rather than being created/destroyed — this keeps `app.js` simple (no templating engine, just `element.hidden = true/false` and `textContent` assignment) and keeps every element's `data-testid` stable for Playwright regardless of application state. `#empty-state` is the only one visible by default; everything else starts hidden and is shown only when its corresponding condition occurs.

### frontend/app.js
**Purpose**: All client-side behavior — validation, the upload request, and rendering every possible outcome.
**Key Functions**: `renderResults()`, `showValidationError()`/`clearValidationError()`, `showErrorBanner()`/`clearErrorBanner()`, `humanizeFieldName()`

**How it works**: The core loop is the submit handler:
```js
if (!file) { showValidationError('Please select a PDF file to upload.'); return; }
if (file.type !== 'application/pdf') { showValidationError('Only PDF files are supported.'); return; }
// ... clear prior state, show loading ...
const response = await fetch('/api/documents', { method: 'POST', body: formData });
const data = await response.json();
if (response.ok) { renderResults(data.extraction); } else { showErrorBanner(data?.detail?.message); }
```
The client-side file-type check is explicitly commented as a UX nicety only — the real security boundary is the backend's `%PDF-` magic-byte check from sprint v1, which can't be bypassed by spoofing `file.type` in the browser. `renderResults()` iterates `Object.entries(extraction)` dynamically rather than hardcoding the 15 field names from the schema, so the frontend can't silently drift out of sync if the backend's field list ever changes — whatever fields the response contains get rendered, each labeled by humanizing its key (`total_capex_usd` → "Total Capex Usd") rather than via a hand-maintained label map. Fields with `confidence: "not_found"` get a distinct label ("Not found in document") and styling class instead of a blank value or literal "null" — the whole point of sprint v1's confidence-tagged schema was to make missing data visible, and this is where that finally becomes visible to a human.

### frontend/styles.css
**Purpose**: Minimal styling — confidence badges, error/empty states, and responsive text wrapping.
**How it works**: Confidence badges are color-coded (`high`=green, `medium`=yellow, `low`=orange, `not_found`=gray) so an analyst can visually scan a results page for weak spots without reading every label. `overflow-wrap: break-word` is set on `body` (inherited by all field text) specifically because real extracted values — long project names, long verbatim source snippets — are attacker-uncontrolled but still arbitrary-length strings that could otherwise force horizontal scrolling on narrow screens.

### backend/app/main.py (modified)
**Purpose**: Serves the frontend as static files alongside the existing API.
**How it works**:
```python
app.include_router(documents_router)
# ...
app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
```
The static mount is registered *last*, after every API route — Starlette matches routes in registration order, so `/health` and `/api/documents` are matched first and the catch-all static mount at `/` only ever serves paths nothing else claimed. This sprint also added `load_dotenv()` at module import time here — a genuine bug fix, not a feature: the app previously never loaded `.env` itself (only the backend's `pytest -m live` tests did, inside the test file), so running `uvicorn app.main:app` exactly as documented would silently 502 on every real extraction. Sprint v2's Task 7 (the real end-to-end smoke test) is what caught this.

### e2e/ (new: package.json, playwright.config.ts, tsconfig.json)
**Purpose**: Playwright/Node tooling for browser-driven E2E tests, kept separate from the Python backend.
**How it works**: `playwright.config.ts` points `baseURL` at `http://127.0.0.1:8000` but does **not** auto-start the backend (`webServer` config) — the backend is a separate Python process outside this Node project, so it's started manually before running tests. `tsconfig.json` (added mid-sprint, during Task 7) enables `strict` mode; running `npx tsc --noEmit` surfaced one pre-existing implicit-`any` parameter in `error-states.spec.ts`, fixed alongside.

### e2e/tests/*.spec.ts (7 files)
Each Playwright spec mocks the backend via `page.route()` except one:
- `upload-form.spec.ts` — form elements exist with correct attributes
- `upload-flow.spec.ts` — loading indicator appears/disappears, timing controlled via a delayed mocked response
- `results-view.spec.ts` — all 15 fields render correctly, `not_found` fields render distinctly
- `validation.spec.ts` — no-file / non-PDF cases show a message and make zero network calls (verified via a route-handler counter)
- `error-states.spec.ts` — parametrized over all 4 documented error codes (400/404/500/502), each rendering `detail.message`
- `responsive-empty-state.spec.ts` — parametrized over 375px/1280px viewports, checking for horizontal overflow (`scrollWidth > clientWidth`) with a deliberately long project name and snippet, not just the trivially-safe bare page
- `full-stack-smoke.spec.ts` — the one spec with **no mocking at all**; uploads a real sprint-v1 sample PDF (`monsoon_wind_laos.pdf`) through the real UI against the real running backend and real Anthropic API. Skipped by default via `test.skip(!process.env.RUN_LIVE_TESTS, ...)`; run explicitly with `RUN_LIVE_TESTS=1 npx playwright test full-stack-smoke.spec.ts`. (An earlier attempt used Playwright's `grepInvert` config plus a `--grep "@live"` CLI flag — that doesn't work, because `grepInvert` and CLI `--grep` combine with AND logic rather than one overriding the other, so a permanent `grepInvert: /@live/` made every `--grep "@live"` invocation match nothing. The env-var `test.skip()` approach is simpler and actually works.)

## Data Flow

1. User selects a PDF and clicks "Analyze".
2. `app.js` validates client-side (file present, `file.type` looks like a PDF) — UX only, not security.
3. `FormData` is POSTed to `/api/documents`; loading indicator shown.
4. Backend (sprint v1, unchanged) runs extract → Claude → normalize → store, returning `{document_id, extraction}` or a structured error.
5. On success, `renderResults()` builds one `.field` block per extracted field, each showing value, confidence badge, and (if present) a quoted source snippet.
6. On failure, `detail.message` renders in the error banner.
7. Either way, the loading indicator is always hidden via `finally`, so the UI never gets stuck mid-request.

## Test Coverage

- **Backend integration** (2 new): `GET /` serves the frontend's HTML; `GET /health` still works after the static mount was added (regression check).
- **E2E (Playwright, mocked)**: 11 tests across 6 spec files — form structure, loading state timing, results rendering (found + not_found), client-side validation (with a zero-network-calls assertion), all 4 documented error codes, and horizontal overflow at 2 viewport widths.
- **E2E (Playwright, live, opt-in)**: 1 test — the real backend, real Anthropic API, real sample PDF, no mocking. Skipped by default; run with `RUN_LIVE_TESTS=1 npx playwright test full-stack-smoke.spec.ts`.
- **Type-checking**: `npx tsc --noEmit` in strict mode, added mid-sprint.
- **Totals**: backend suite is now 28 tests (26 default + this sprint's live tests remain at 7, unchanged from v1); e2e suite is 12 tests (11 run by default, 1 opt-in).

## Security Measures

- Client-side file-type validation is explicitly documented (in code comments) as a UX nicety only — the backend's `%PDF-` magic-byte check remains the actual security boundary, unchanged from sprint v1.
- No new secrets or credentials introduced; `ANTHROPIC_API_KEY` still only lives in `backend/.env` (gitignored).
- `npm audit`: 0 vulnerabilities throughout the sprint (checked after every task).
- `semgrep --config auto`: clean throughout the sprint, across both the Python backend and the new frontend/e2e code.
- `pip-audit`: clean throughout (no backend dependency changes this sprint).

## Known Limitations

- **No CORS needed and none configured** — this only holds because the frontend is served from the same FastAPI process. If the frontend is ever split out to its own server/host, CORS middleware would need to be added.
- **No automatic backend startup for E2E tests** — `playwright.config.ts` has no `webServer` entry; the backend must be started manually (`uvicorn app.main:app`) before running any e2e test, mocked or live. This is documented in a comment but not automated.
- **No retry or cancel affordance** — if a request is slow or fails, the user's only option is to resubmit; there's no cancel button for an in-flight request.
- **Client-side validation is minimal** — only checks presence and MIME type, nothing about file size (the backend still enforces its 20MB cap correctly, but the UI won't warn before hitting it).
- **No accessibility audit performed** — form labels, ARIA roles, and keyboard navigation haven't been explicitly reviewed.
- **Single-document session only** — no history/list view (explicitly deferred, per the PRD); `GET /api/documents/{id}` from sprint v1 exists but nothing in the UI links to it yet.
- **README.md and the AI-assistant conversation log are still outstanding** — both required deliverables per the brief, intentionally deferred by the user to the end of the project rather than any specific sprint.

## What's Next

- Address the two outstanding required deliverables (README.md, AI conversation log) whenever the project is being wrapped up.
- Consider a v3 focused on broader reliability/quality: splitting compound fields like `debt_equity_ratio` into strictly-typed sub-fields (surfaced in sprint v1's real-document testing), testing against a real TerraWatt-provided proposal, an accessibility pass, and deciding whether persistence needs to move beyond the in-memory store before this could be considered production-ready.
