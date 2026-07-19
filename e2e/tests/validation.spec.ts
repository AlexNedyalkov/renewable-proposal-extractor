import { test, expect } from '@playwright/test';

test('shows a validation message and makes no request when no file is selected', async ({ page }) => {
  let requestCount = 0;
  await page.route('**/api/documents', (route) => {
    requestCount++;
    return route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });

  await page.goto('/');
  await page.getByTestId('submit-button').click();

  const validationError = page.getByTestId('validation-error');
  await expect(validationError).toBeVisible();
  await expect(validationError).toContainText('select a PDF file');
  expect(requestCount).toBe(0);

  await page.screenshot({ path: 'tests/screenshots/task5-step1-no-file-selected.png' });
});

test('shows a validation message and makes no request when a non-PDF file is selected', async ({ page }) => {
  let requestCount = 0;
  await page.route('**/api/documents', (route) => {
    requestCount++;
    return route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });

  await page.goto('/');
  await page.getByTestId('file-input').setInputFiles({
    name: 'notes.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from('just some plain text, not a pdf'),
  });
  await page.getByTestId('submit-button').click();

  const validationError = page.getByTestId('validation-error');
  await expect(validationError).toBeVisible();
  await expect(validationError).toContainText('Only PDF files are supported');
  expect(requestCount).toBe(0);

  await page.screenshot({ path: 'tests/screenshots/task5-step2-non-pdf-file-selected.png' });
});
