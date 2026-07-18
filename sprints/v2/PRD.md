# Sprint v2 — PRD

## 1. Sprint Overview
Build the frontend for the AI-Powered Document Analyzer: a plain HTML/CSS/JS page, served directly by the existing FastAPI backend, that lets an analyst upload a proposal PDF and see the extracted results (including confidence and source snippets) without leaving the page.

Note: README.md and the AI-assistant conversation log are both still-missing required deliverables per the brief, but the user has chosen to handle them at the very end of the project (after all sprints), not in v2. They are out of scope here — see §5.

## 2. Goals
- A single-page frontend, served by FastAPI as static files (same origin, no CORS needed), lets a user upload a PDF and view results in one flow.
- A visible loading state covers the multi-second gap while the backend calls Claude.
- All 15 extracted fields render clearly, with `not_found` fields visually distinct from found ones — not just blank or "null".
- Backend error responses (400/404/500/502) surface as a readable message, never a blank page or raw JSON.

## 3. User Stories
- As an analyst, I want to upload a PDF proposal through a web page, so that I don't need curl or Postman to use the tool.
- As an analyst, I want to see a loading indicator while my document is processed, so that I know the app is working during the Claude call.
- As an analyst, I want to see every extracted field with its confidence level and supporting quote, so that I can quickly judge which values to double-check manually.
- As an analyst, I want a clear error message when something goes wrong, so that I understand what to fix instead of seeing a blank page.

## 4. Technical Architecture

**Stack**: Plain HTML/CSS/JS + Fetch API (no framework, no build step). Served by the existing FastAPI app via a `StaticFiles` mount — same origin as the API, so no CORS configuration is needed. Playwright (Node.js, already available locally) for E2E testing, per the `/dev` skill's rule that UI tasks get Playwright tests with screenshots.

**Directory layout** (new):
```
frontend/
  index.html
  styles.css
  app.js
e2e/
  package.json
  playwright.config.ts
  tests/
    *.spec.ts
    screenshots/
```

**Component diagram**:
```
+------------------+        GET /                 +---------------------------+
|   Browser         |<-----------------------------|  FastAPI StaticFiles      |
|  index.html/js/css|----------------------------->|  mount (serves frontend/) |
+------------------+                               +---------------------------+
        |
        | fetch POST /api/documents (FormData: file)
        v
+-------------------------------------------------------------+
|         Existing FastAPI backend (sprint v1, unchanged)     |
|   POST /api/documents        GET /api/documents/{id}         |
+-------------------------------------------------------------+
```

**Data flow**: User selects a PDF and submits the form → `app.js` builds a `FormData` and does `fetch('/api/documents', {method: 'POST', body: formData})` → a loading state is shown → on `200`, the 15 fields render (value, confidence badge, source snippet, `not_found` fields styled distinctly) → on a non-200 response, the JSON body's `detail.message` renders in an error banner.

## 5. Out of Scope
- **README.md and the AI-assistant conversation log** — both required deliverables per the brief, but explicitly deferred by the user to the end of the project (after all sprints), not this sprint.
- History/list view of past analyses (explicitly deferred; `GET /api/documents/{id}` exists if deep-linking is needed later)
- Authentication
- Any change to backend extraction logic (sprint v1's pipeline is untouched)
- A JS framework or build tooling (React, Vite, bundlers) — plain JS only, per the original project decision
- Deployment/hosting
- Broader security review / accessibility audit (v3)

## 6. Dependencies
- Sprint v1 backend, complete and working (`backend/`)
- Node.js and npm available locally for Playwright (confirmed: Node v24.16.0, npm 11.13.0)
