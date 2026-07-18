import { test, expect } from '@playwright/test';

test('upload form has a PDF file input and a submit button', async ({ page }) => {
  await page.goto('/');

  const fileInput = page.getByTestId('file-input');
  const submitButton = page.getByTestId('submit-button');

  await expect(fileInput).toBeAttached();
  await expect(fileInput).toHaveAttribute('type', 'file');
  await expect(fileInput).toHaveAttribute('accept', 'application/pdf');
  await expect(submitButton).toBeVisible();

  await page.screenshot({ path: 'tests/screenshots/task2-step1-upload-form.png' });
});
