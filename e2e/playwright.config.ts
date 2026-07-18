import { defineConfig } from '@playwright/test';

// These tests exercise the frontend against the real backend, which must
// be started separately (e.g. `uvicorn app.main:app` from backend/) before
// running `npx playwright test` — no automatic webServer startup, since
// the backend is a separate Python process outside this Node project.
export default defineConfig({
  testDir: './tests',
  use: {
    baseURL: 'http://127.0.0.1:8000',
  },
});
