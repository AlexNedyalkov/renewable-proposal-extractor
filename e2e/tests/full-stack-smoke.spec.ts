import path from 'node:path';
import { test, expect } from '@playwright/test';

// Requires the backend to be running with a real ANTHROPIC_API_KEY
// configured (backend/.env) — no network mocking here, unlike every other
// spec in this project. Costs money (real Anthropic API call), so it's
// skipped by default — mirroring the backend's `pytest -m live` pattern.
// Run explicitly with:
//   RUN_LIVE_TESTS=1 npx playwright test full-stack-smoke.spec.ts
test('uploads a real sample PDF and renders real extracted results', async ({ page }) => {
  test.skip(!process.env.RUN_LIVE_TESTS, 'Live test skipped by default. Set RUN_LIVE_TESTS=1 to run.');
  test.setTimeout(120_000);

  const samplePdfPath = path.resolve(
    __dirname,
    '..',
    '..',
    'backend',
    'tests',
    'fixtures',
    'real_samples',
    'monsoon_wind_laos.pdf',
  );

  await page.goto('/');
  await page.getByTestId('file-input').setInputFiles(samplePdfPath);
  await page.getByTestId('submit-button').click();

  await expect(page.getByTestId('loading')).toBeVisible();

  const results = page.getByTestId('results');
  await expect(results).toBeVisible({ timeout: 45_000 });
  await expect(page.getByTestId('loading')).toBeHidden();
  await expect(page.getByTestId('error-banner')).toBeHidden();

  const projectName = page.getByTestId('field-project_name-value');
  await expect(projectName).not.toHaveText('Not found in document');
  await expect(projectName).toContainText(/monsoon/i);

  await expect(page.getByTestId('field-installed_capacity_mw-confidence')).not.toHaveText('not_found');

  await page.screenshot({ path: 'tests/screenshots/task7-step1-full-stack-smoke.png', fullPage: true });
});
