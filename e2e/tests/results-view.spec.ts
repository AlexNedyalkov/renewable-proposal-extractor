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

test('renders extraction results, including distinct styling for not_found fields', async ({ page }) => {
  await page.route('**/api/documents', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ document_id: 'test-id', extraction: CANNED_EXTRACTION }),
    })
  );

  await page.goto('/');
  await page.getByTestId('file-input').setInputFiles({
    name: 'proposal.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('%PDF-1.4 fake content for testing'),
  });
  await page.getByTestId('submit-button').click();

  const results = page.getByTestId('results');
  await expect(results).toBeVisible();

  // A found field renders its value, confidence, and supporting snippet.
  await expect(page.getByTestId('field-project_name-value')).toHaveText('Prairie Wind Energy Project');
  await expect(page.getByTestId('field-project_name-confidence')).toHaveText('high');
  await expect(page.getByTestId('field-project_name-snippet')).toContainText('Prairie Wind Energy Project');

  // All 16 schema fields are present.
  for (const fieldName of Object.keys(CANNED_EXTRACTION)) {
    await expect(page.getByTestId(`field-${fieldName}`)).toBeAttached();
  }

  // A not_found field renders a distinct label, not blank or literal "null".
  const notFoundValue = page.getByTestId('field-total_capex_usd-value');
  await expect(notFoundValue).toHaveText('Not found in document');
  await expect(notFoundValue).toHaveClass(/not-found/);
  await expect(page.getByTestId('field-total_capex_usd-confidence')).toHaveText('not_found');

  await page.screenshot({ path: 'tests/screenshots/task4-step1-results-rendered.png', fullPage: true });
});
