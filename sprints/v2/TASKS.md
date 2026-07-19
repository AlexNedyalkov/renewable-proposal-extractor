# Sprint v2 — Tasks

- [x] Task 1: Project setup — frontend scaffold, static mount, Playwright tooling (P0)
    Acceptance: `frontend/index.html` (minimal shell), `frontend/styles.css`, `frontend/app.js` exist; FastAPI mounts `frontend/` as static files so `GET /` returns 200 with the HTML shell, without breaking existing `/health` or `/api/documents` routes; `e2e/package.json` + Playwright installed, `npx playwright test` runs cleanly with 0 tests.
    Files: backend/app/main.py, frontend/index.html, frontend/styles.css, frontend/app.js, e2e/package.json, e2e/playwright.config.ts
    Completed: 2026-07-18 — StaticFiles mounted at "/" *after* the API routes so specific paths (/health, /api/documents) are matched first; verified with both TestClient and a live uvicorn boot (curl to /, /styles.css, /health all correct). Note on acceptance wording: `npx playwright test` with zero spec files actually exits 1 ("No tests found") — that's Playwright's correct behavior, not a broken install; verified the toolchain is genuinely functional end-to-end with a throwaway spec (ran, passed, then deleted), so tests/ stays empty until Task 2's first real spec. 2 new backend integration tests (root serves HTML, health still works post-mount). Security: semgrep clean, pip-audit clean, npm audit clean (0 vulnerabilities in the new e2e/ Node project).

- [x] Task 2: Upload form UI (P0)
    Acceptance: `index.html` has a file input (`accept="application/pdf"`) and a submit button, each with `data-testid` attributes. Playwright test loads the page, confirms both elements are present, and saves a screenshot to `e2e/tests/screenshots/task2-step1-upload-form.png`.
    Files: frontend/index.html, e2e/tests/upload-form.spec.ts, e2e/tests/screenshots/
    Completed: 2026-07-18 — Added a plain `<form>` with a `data-testid="file-input"` file input (accept=application/pdf) and `data-testid="submit-button"`. Playwright test run against a live local uvicorn instance (started/stopped manually for this task), confirmed red before the form existed, green after, screenshot saved. Backend test suite unaffected (28 passed). Security: semgrep clean, pip-audit clean, npm audit clean.

- [x] Task 3: Wire upload submission + loading state (P0)
    Acceptance: Submitting the form sends a `fetch POST` with `FormData` to `/api/documents`; a loading indicator (`data-testid="loading"`) appears while the request is in flight and disappears once it resolves. Playwright test intercepts the network call (`page.route`) to control timing, asserts the loading state appears then disappears, with before/after screenshots.
    Files: frontend/app.js, e2e/tests/upload-flow.spec.ts, e2e/tests/screenshots/
    Completed: 2026-07-18 — Form submit handler builds FormData, toggles the `hidden` attribute on the loading element around the fetch call (via try/finally, so it always hides even on failure). Response handling is currently just console.log — actual result/error rendering are Tasks 4 and 6. Playwright test mocks the network call's timing via page.route to deterministically observe loading appear/disappear; confirmed red before the handler existed, green after; 3 screenshots saved. Full e2e suite (2 tests) and backend suite (28 tests) both pass. Security: semgrep clean, pip-audit clean, npm audit clean.

- [x] Task 4: Render extraction results, including not_found fields (P0)
    Acceptance: On a successful response, all 15 fields render with their value, confidence badge, and source snippet, each with a `data-testid`; fields with `confidence: "not_found"` render with a visibly distinct style/label (e.g. "Not found in document") rather than blank or literal "null". Playwright test intercepts the API call with a canned response containing a mix of found and not_found fields, asserts both render correctly, with a screenshot.
    Files: frontend/app.js, frontend/index.html, frontend/styles.css, e2e/tests/results-view.spec.ts, e2e/tests/screenshots/
    Completed: 2026-07-19 — renderResults() iterates Object.entries(extraction) dynamically rather than hardcoding the 15 field names, so it can't drift from the backend schema if fields are ever added/removed. Field labels are derived from the key (e.g. `total_capex_usd` -> "Total Capex Usd") rather than a hand-maintained label map, same reasoning. not_found fields get a distinct label ("Not found in document"), a `.field-value-not-found` class, and no snippet row (since source_snippet is null); confidence badges are color-coded per level. Playwright test uses a canned response mixing found/not_found across all 15 fields; confirmed red before rendering existed. Full e2e suite (3 tests) and backend suite (28 tests) both pass. Security: semgrep clean, pip-audit clean, npm audit clean.

- [x] Task 5: Client-side validation before upload (P0)
    Acceptance: Submitting with no file selected, or a non-PDF file, shows an inline validation message and does not call the API (client-side UX nicety only — the backend's magic-byte check remains the real security boundary). Playwright test asserts the message appears and confirms no network request was made.
    Files: frontend/app.js, e2e/tests/validation.spec.ts, e2e/tests/screenshots/
    Completed: 2026-07-19 — Validation checks (no file / non-PDF `file.type`) run before building FormData and return early, so fetch is never called; a code comment makes explicit that this is a UX nicety only, not the security boundary (that's the backend's magic-byte check from sprint v1). 2 Playwright tests, each asserting zero network calls via a route-handler counter; confirmed red before validation existed. Full e2e suite (5 tests) and backend suite (28 tests) both pass. Security: semgrep clean, pip-audit clean, npm audit clean.

- [ ] Task 6: Render backend error responses (P0)
    Acceptance: When the backend returns a 400/404/500/502 structured error, the UI shows that response's `detail.message` in a visible error banner instead of a blank page or silent console failure. Playwright test intercepts the API call returning each error status in turn, asserts the message renders, with a screenshot per case.
    Files: frontend/app.js, frontend/styles.css, e2e/tests/error-states.spec.ts, e2e/tests/screenshots/

- [ ] Task 7: End-to-end smoke test against the real backend (P1)
    Acceptance: A Playwright test (no network mocking) drives the actual running FastAPI app, uploads one of sprint v1's real or synthetic sample PDFs through the real UI, and asserts real extracted results render. Marked/tagged as opt-in (costs money via the real Anthropic API), consistent with the backend's `pytest -m live` pattern — e.g. a separate `npx playwright test --grep @live` invocation, excluded from the default test run.
    Files: e2e/tests/full-stack-smoke.spec.ts, e2e/tests/screenshots/

- [ ] Task 8: Basic responsive/empty-state polish (P1)
    Acceptance: Page has a sensible initial empty state (no results yet) with brief instructions; layout doesn't overflow horizontally at common viewport widths (e.g. 375px and 1280px), checked manually or via the existing Playwright screenshots at both sizes.
    Files: frontend/index.html, frontend/styles.css
