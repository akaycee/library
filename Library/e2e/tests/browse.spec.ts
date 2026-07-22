import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

async function adminLogin(page: Page) {
  await page.goto('/login');
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('Admin12345');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page.getByRole('link', { name: 'Catalog', exact: true })).toBeVisible();
}

async function seed(page: Page, titleName: string, locName: string) {
  // Create a location
  await page.getByRole('link', { name: 'Locations', exact: true }).click();
  await page.getByRole('button', { name: /add location/i }).click();
  let dlg = page.getByRole('dialog');
  await dlg.getByLabel(/^Name/).fill(locName);
  await dlg.getByRole('button', { name: /^save$/i }).click();
  await expect(page.getByRole('treeitem', { name: locName })).toBeVisible();

  // Create a title + one copy
  await page.getByRole('link', { name: 'Catalog', exact: true }).click();
  await page.getByRole('button', { name: /add title/i }).click();
  dlg = page.getByRole('dialog');
  await dlg.getByLabel(/^Title/).fill(titleName);
  await dlg.getByRole('button', { name: /^save$/i }).click();
  await page.getByRole('link', { name: titleName }).click();
  await page.getByRole('button', { name: /add copy/i }).click();
  dlg = page.getByRole('dialog');
  await dlg.getByLabel('Location').click();
  await page.getByRole('option', { name: new RegExp(locName) }).click();
  await dlg.getByRole('button', { name: /^save$/i }).click();
  await expect(page.getByText(/LIB-\d+/)).toBeVisible();
}

test('a borrower can browse and search the catalog', async ({ page, browser }) => {
  const unique = `Zephyr ${Date.now()}`;
  await adminLogin(page);
  await seed(page, unique, `BrowseLoc ${Date.now()}`);

  // Borrower browses in a separate context
  const ctx = await browser.newContext({ baseURL: 'http://127.0.0.1:8123' });
  const borrower = await ctx.newPage();
  const uname = `bor_${Date.now()}`;
  await borrower.goto('/signup');
  await borrower.getByLabel('Username').fill(uname);
  await borrower.getByLabel('Password').fill('abcd1234');
  await borrower.getByRole('button', { name: /create account/i }).click();
  await expect(borrower.getByText(/signed in as borrower/i)).toBeVisible();

  await borrower.getByRole('link', { name: 'Browse', exact: true }).click();
  await expect(borrower).toHaveURL(/\/browse$/);
  await expect(borrower.getByRole('heading', { name: unique })).toBeVisible();
  await expect(borrower.getByText(/1 of 1 available/i)).toBeVisible();

  // Search narrows results
  await borrower.getByLabel('Search the catalog').fill(unique);
  await borrower.getByRole('button', { name: /^search$/i }).click();
  await expect(borrower.getByRole('heading', { name: unique })).toBeVisible();

  // No match shows empty state
  await borrower.getByLabel('Search the catalog').fill('nonexistent-xyz');
  await borrower.getByRole('button', { name: /^search$/i }).click();
  await expect(borrower.getByText(/no titles match/i)).toBeVisible();

  await ctx.close();
});

test('browse page has no serious accessibility violations', async ({ page }) => {
  await adminLogin(page);
  await page.getByRole('link', { name: 'Browse', exact: true }).click();
  const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
  const serious = results.violations.filter((v) => ['serious', 'critical'].includes(v.impact ?? ''));
  expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
});
