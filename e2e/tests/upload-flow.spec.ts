import { test, expect } from '@playwright/test';

test('shows a loading indicator while the upload request is in flight', async ({ page }) => {
  await page.route('**/api/documents', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 500));
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ document_id: 'test-id', extraction: {} }),
    });
  });

  await page.goto('/');

  const loading = page.getByTestId('loading');
  await expect(loading).toBeHidden();

  await page.getByTestId('file-input').setInputFiles({
    name: 'proposal.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('%PDF-1.4 fake content for testing'),
  });

  await page.screenshot({ path: 'tests/screenshots/task3-step1-before-submit.png' });

  await page.getByTestId('submit-button').click();

  await expect(loading).toBeVisible();
  await page.screenshot({ path: 'tests/screenshots/task3-step2-loading-visible.png' });

  await expect(loading).toBeHidden({ timeout: 3000 });
  await page.screenshot({ path: 'tests/screenshots/task3-step3-loading-hidden.png' });
});
