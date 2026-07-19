import { test, expect, type Page } from '@playwright/test';

const VIEWPORTS = [
  { width: 375, height: 667, label: 'mobile' },
  { width: 1280, height: 800, label: 'desktop' },
];

const CANNED_EXTRACTION = {
  project_name: {
    value: 'A Very Long Renewable Energy Project Name That Could Plausibly Wrap Across Multiple Lines On A Narrow Screen',
    confidence: 'high',
    source_snippet:
      'This is a deliberately long supporting source snippet meant to stress-test text wrapping and horizontal overflow handling on narrow viewports such as 375px wide mobile screens.',
  },
  location: { value: 'Story County, Iowa, USA', confidence: 'high', source_snippet: 'located in Story County, Iowa' },
  technology_type: { value: 'Onshore Wind', confidence: 'high', source_snippet: '220 MW onshore wind' },
  installed_capacity_mw: { value: 220, confidence: 'high', source_snippet: 'total installed capacity of 220 MW' },
  expected_annual_generation_mwh: { value: 650000, confidence: 'medium', source_snippet: 'approximately 650,000 MWh' },
  commercial_operation_date: { value: 'March 2028', confidence: 'high', source_snippet: 'commercial operation in March 2028' },
  developer_sponsor: { value: 'Meadowlark Renewables LLC', confidence: 'high', source_snippet: 'developed by Meadowlark Renewables LLC' },
  total_capex_usd: { value: null, confidence: 'not_found', source_snippet: null },
  capex_per_mw: { value: null, confidence: 'not_found', source_snippet: null },
  expected_irr_percent: { value: null, confidence: 'not_found', source_snippet: null },
  payback_period_years: { value: null, confidence: 'not_found', source_snippet: null },
  lcoe_usd_per_mwh: { value: null, confidence: 'not_found', source_snippet: null },
  ppa_price_usd_per_mwh: { value: 27, confidence: 'low', source_snippet: 'a fixed price of $27 per MWh' },
  ppa_term_years: { value: 15, confidence: 'high', source_snippet: '15-year power purchase agreement' },
  debt_equity_ratio: { value: '65:35', confidence: 'medium', source_snippet: 'debt-to-equity ratio of 65:35' },
};

async function hasHorizontalOverflow(page: Page): Promise<boolean> {
  return page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
}

for (const { width, height, label } of VIEWPORTS) {
  test(`shows an empty state with no horizontal overflow at ${label} (${width}px)`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    await page.goto('/');

    const emptyState = page.getByTestId('empty-state');
    await expect(emptyState).toBeVisible();
    await expect(emptyState).toContainText('No document analyzed yet');

    expect(await hasHorizontalOverflow(page)).toBe(false);
    await page.screenshot({ path: `tests/screenshots/task8-step1-empty-state-${label}.png` });

    await page.route('**/api/documents', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ document_id: 'test-id', extraction: CANNED_EXTRACTION }),
      })
    );

    await page.getByTestId('file-input').setInputFiles({
      name: 'proposal.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4 fake content for testing'),
    });
    await page.getByTestId('submit-button').click();

    await expect(page.getByTestId('results')).toBeVisible();
    await expect(emptyState).toBeHidden();

    expect(await hasHorizontalOverflow(page)).toBe(false);
    await page.screenshot({ path: `tests/screenshots/task8-step2-results-${label}.png`, fullPage: true });
  });
}
