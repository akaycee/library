import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

async function adminLogin(page: Page) {
  await page.goto('/login');
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('Admin12345');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page.getByRole('link', { name: 'Catalog', exact: true })).toBeVisible();
}

async function createLocation(page: Page, name: string) {
  await page.getByRole('link', { name: 'Locations', exact: true }).click();
  await page.getByRole('button', { name: /add location/i }).click();
  const dlg = page.getByRole('dialog');
  await dlg.getByLabel(/^Name/).fill(name);
  await dlg.getByRole('button', { name: /^save$/i }).click();
  await expect(page.getByRole('treeitem', { name })).toBeVisible();
}

async function addTitle(page: Page, name: string) {
  await page.getByRole('link', { name: 'Catalog', exact: true }).click();
  await expect(page).toHaveURL(/\/catalog$/);
  await page.getByRole('button', { name: /add title/i }).click();
  const dlg = page.getByRole('dialog');
  await dlg.getByLabel(/^Title/).fill(name);
  await dlg.getByRole('button', { name: /^save$/i }).click();
}

async function addCopy(page: Page, locationName: string) {
  await page.getByRole('button', { name: /add copy/i }).click();
  const dlg = page.getByRole('dialog');
  await dlg.getByLabel('Location').click();
  await page.getByRole('option', { name: new RegExp(locationName) }).click();
  await dlg.getByRole('button', { name: /^save$/i }).click();
}

test('staff catalogs a title with copies that get barcodes', async ({ page }) => {
  await adminLogin(page);
  const loc = `Catalog Room ${Date.now()}`;
  await createLocation(page, loc);
  await addTitle(page, "Charlotte's Web");

  await page.getByRole('link', { name: "Charlotte's Web" }).click();
  await expect(page).toHaveURL(/\/catalog\/.+/);

  await addCopy(page, loc);
  await addCopy(page, loc);

  const barcodes = page.getByText(/LIB-\d+/);
  await expect(barcodes).toHaveCount(2);
});

test('staff changes a copy status and deletes a copy', async ({ page }) => {
  await adminLogin(page);
  const loc = `Catalog Storage ${Date.now()}`;
  await createLocation(page, loc);
  await addTitle(page, 'The Hobbit');
  await page.getByRole('link', { name: 'The Hobbit' }).click();
  await addCopy(page, loc);

  // Change status to lost
  const row = page.getByRole('row').filter({ hasText: /LIB-/ });
  await row.getByRole('combobox').click();
  await page.getByRole('option', { name: /^lost$/i }).click();
  await expect(row.getByRole('combobox')).toContainText(/lost/i);

  // Delete the copy
  await row.getByRole('button', { name: /^delete$/i }).click();
  await expect(page.getByText(/LIB-\d+/)).toHaveCount(0);
});

test('a title with copies cannot be deleted until empty', async ({ page }) => {
  await adminLogin(page);
  const loc = `Catalog Wing ${Date.now()}`;
  await createLocation(page, loc);
  await addTitle(page, 'Matilda');
  await page.getByRole('link', { name: 'Matilda' }).click();
  await addCopy(page, loc);

  // Attempt to delete the title -> blocked
  await page.getByRole('button', { name: /delete title/i }).click();
  await page.getByRole('dialog').getByRole('button', { name: /^delete$/i }).click();
  await expect(page.getByText(/still has copies/i)).toBeVisible();
});

test('staff edits a title', async ({ page }) => {
  await adminLogin(page);
  await addTitle(page, 'Old Title');
  await page.getByRole('link', { name: 'Old Title' }).click();
  await page.getByRole('button', { name: /^edit$/i }).click();
  const dlg = page.getByRole('dialog');
  await dlg.getByLabel(/^Author/).fill('Jane Doe');
  await dlg.getByRole('button', { name: /^save$/i }).click();
  await expect(page.getByText(/Jane Doe/)).toBeVisible();
});

test('catalog pages have no serious accessibility violations', async ({ page }) => {
  await adminLogin(page);
  await page.getByRole('link', { name: 'Catalog', exact: true }).click();
  const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
  const serious = results.violations.filter((v) => ['serious', 'critical'].includes(v.impact ?? ''));
  expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
});
