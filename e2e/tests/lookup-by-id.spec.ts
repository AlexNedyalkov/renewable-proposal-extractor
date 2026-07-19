import path from 'node:path';
import { test, expect } from '@playwright/test';

const CANNED_EXTRACTION = {
  project_name: { value: 'Prairie Wind Energy Project', confidence: 'high', source_snippet: 'The Prairie Wind Energy Project is a 220 MW onshore wind facility.' },
  location: { value: 'Story County, Iowa, USA', confidence: 'high', source_snippet: 'located in Story County, Iowa, USA' },
  technology_type: { value: 'Onshore Wind', confidence: 'high', source_snippet: '220 MW onshore wind generation facility' },
  installed_capacity_mw: { value: 220, confidence: 'high', source_snippet: 'total installed capacity of 220 MW' },
  expected_annual_generation_mwh: { value: 650000, confidence: 'medium', source_snippet: 'approximately 650,000 MWh annually' },
  commercial_operation_date: { value: 'March 2028', confidence: 'high', source_snippet: 'commercial operation in March 2028' },
  developer_sponsor: { value: 'Meadowlark Renewables LLC', confidence: 'high', source_snippet: 'developed by Meadowlark Renewables LLC' },
  total_capex_usd: { value: null, confidence: 'not_found', source_snippet: null },
  capex_per_mw: { value: null, confidence: 'not_found', source_snippet: null },
  expected_irr_percent: { value: null, confidence: 'not_found', source_snippet: null },
  payback_period_years: { value: null, confidence: 'not_found', source_snippet: null },
  lcoe_usd_per_mwh: { value: null, confidence: 'not_found', source_snippet: null },
  ppa_price_usd_per_mwh: { value: 27, confidence: 'low', source_snippet: 'a fixed price of $27 per MWh' },
  ppa_term_years: { value: 15, confidence: 'high', source_snippet: 'secured a 15-year power purchase agreement' },
  debt_percent: { value: 65, confidence: 'medium', source_snippet: 'debt-to-equity ratio of 65:35' },
  equity_percent: { value: 35, confidence: 'medium', source_snippet: 'debt-to-equity ratio of 65:35' },
};

test('looking up a known document id renders its stored results', async ({ page }) => {
  await page.route('**/api/documents/*', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ document_id: 'abc-123', extraction: CANNED_EXTRACTION }),
    })
  );

  await page.goto('/');
  await page.getByTestId('lookup-id-input').fill('abc-123');
  await page.getByTestId('lookup-submit-button').click();

  const results = page.getByTestId('results');
  await expect(results).toBeVisible();
  await expect(page.getByTestId('field-project_name-value')).toHaveText('Prairie Wind Energy Project');

  await page.screenshot({ path: 'tests/screenshots/task5-step1-lookup-found.png' });
});

test('looking up an unknown document id shows a not-found message', async ({ page }) => {
  await page.route('**/api/documents/*', (route) =>
    route.fulfill({
      status: 404,
      contentType: 'application/json',
      body: JSON.stringify({
        detail: { error: 'document_not_found', message: "No document found with id 'does-not-exist'." },
      }),
    })
  );

  await page.goto('/');
  await page.getByTestId('lookup-id-input').fill('does-not-exist');
  await page.getByTestId('lookup-submit-button').click();

  const errorBanner = page.getByTestId('error-banner');
  await expect(errorBanner).toBeVisible();
  await expect(errorBanner).toContainText('No document found');

  await page.screenshot({ path: 'tests/screenshots/task5-step2-lookup-not-found.png' });
});

test('shows the document ID after a successful upload, so it can be used for a later lookup', async ({ page }) => {
  await page.route('**/api/documents', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ document_id: 'mocked-doc-id-789', extraction: CANNED_EXTRACTION }),
    })
  );

  await page.goto('/');
  await page.getByTestId('file-input').setInputFiles({
    name: 'proposal.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('%PDF-1.4 fake content for testing'),
  });
  await page.getByTestId('submit-button').click();

  await expect(page.getByTestId('results')).toBeVisible();
  await expect(page.getByTestId('document-id-value')).toHaveText('mocked-doc-id-789');

  await page.screenshot({ path: 'tests/screenshots/task8-step1-document-id-shown.png' });
});

// Requires the backend to be running with a real ANTHROPIC_API_KEY
// configured -- no network mocking here. Costs money (2 real API calls:
// one upload, one implicit via the lookup reusing the stored result --
// actually the lookup itself is free, it just reads the in-memory store).
// Skipped by default; run explicitly with:
//   RUN_LIVE_TESTS=1 npx playwright test lookup-by-id.spec.ts
test('a real uploaded document can be retrieved again by ID through the UI', async ({ page }) => {
  test.skip(!process.env.RUN_LIVE_TESTS, 'Live test skipped by default. Set RUN_LIVE_TESTS=1 to run.');
  test.setTimeout(60_000);

  const samplePdfPath = path.resolve(
    __dirname,
    '..',
    '..',
    'backend',
    'tests',
    'fixtures',
    'real_samples',
    'aj_solar_india.pdf',
  );

  await page.goto('/');
  await page.getByTestId('file-input').setInputFiles(samplePdfPath);
  await page.getByTestId('submit-button').click();

  await expect(page.getByTestId('results')).toBeVisible({ timeout: 45_000 });
  const documentId = await page.getByTestId('document-id-value').textContent();
  const uploadedProjectName = await page.getByTestId('field-project_name-value').textContent();
  expect(documentId).toBeTruthy();
  expect(uploadedProjectName).toContain('AJ Solar');

  // Reload to a clean slate, then look the same document up by ID instead
  // of uploading again.
  await page.reload();
  await expect(page.getByTestId('empty-state')).toBeVisible();

  await page.getByTestId('lookup-id-input').fill(documentId!);
  await page.getByTestId('lookup-submit-button').click();

  await expect(page.getByTestId('results')).toBeVisible();
  const lookedUpProjectName = await page.getByTestId('field-project_name-value').textContent();
  expect(lookedUpProjectName).toBe(uploadedProjectName);

  await page.screenshot({ path: 'tests/screenshots/task8-step2-real-lookup-matches-upload.png', fullPage: true });
});
