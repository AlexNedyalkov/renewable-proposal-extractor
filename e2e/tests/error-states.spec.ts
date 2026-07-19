import { test, expect, type Page } from '@playwright/test';

async function uploadAndExpectFile(page: Page) {
  await page.getByTestId('file-input').setInputFiles({
    name: 'proposal.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('%PDF-1.4 fake content for testing'),
  });
  await page.getByTestId('submit-button').click();
}

const CASES = [
  { status: 400, error: 'invalid_file_type', message: 'Only PDF files are supported.', step: 1 },
  { status: 404, error: 'document_not_found', message: "No document found with id 'abc123'.", step: 2 },
  { status: 500, error: 'pdf_processing_failed', message: 'Failed to process the uploaded PDF.', step: 3 },
  { status: 502, error: 'extraction_service_error', message: 'The extraction service failed to process this document.', step: 4 },
];

for (const { status, error, message, step } of CASES) {
  test(`shows the backend's error message for a ${status} response`, async ({ page }) => {
    await page.route('**/api/documents', (route) =>
      route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify({ detail: { error, message } }),
      })
    );

    await page.goto('/');
    await uploadAndExpectFile(page);

    const errorBanner = page.getByTestId('error-banner');
    await expect(errorBanner).toBeVisible();
    await expect(errorBanner).toContainText(message);

    await page.screenshot({ path: `tests/screenshots/task6-step${step}-error-${status}.png` });
  });
}
