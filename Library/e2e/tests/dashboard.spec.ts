import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const BASE = 'http://127.0.0.1:8123';

async function adminLogin(page: Page) {
  await page.goto('/login');
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('Admin12345');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page.getByRole('link', { name: 'Dashboard', exact: true })).toBeVisible();
}

/** Creates a location, title, and one copy; returns the copy's barcode. */
async function seedCopy(page: Page, titleName: string, locName: string): Promise<string> {
  await page.getByRole('link', { name: 'Locations', exact: true }).click();
  await page.getByRole('button', { name: /add location/i }).click();
  let dlg = page.getByRole('dialog');
  await dlg.getByLabel(/^Name/).fill(locName);
  await dlg.getByRole('button', { name: /^save$/i }).click();
  await expect(page.getByRole('treeitem', { name: locName })).toBeVisible();

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
  const barcode = (await page.getByText(/LIB-\d+/).first().innerText()).trim();
  return barcode;
}

test('dashboard shows stats and recent activity after a checkout', async ({ page, browser }) => {
  // Borrower self-registers in a separate context.
  const ctx = await browser.newContext({ baseURL: BASE });
  const borrower = await ctx.newPage();
  const uname = `dbor_${Date.now()}`;
  await borrower.goto('/signup');
  await borrower.getByLabel('Username').fill(uname);
  await borrower.getByLabel('Password').fill('abcd1234');
  await borrower.getByRole('button', { name: /create account/i }).click();
  await expect(borrower.getByText(/signed in as borrower/i)).toBeVisible();
  await ctx.close();

  const titleName = `Dash Book ${Date.now()}`;
  await adminLogin(page);
  const barcode = await seedCopy(page, titleName, `Dash Loc ${Date.now()}`);

  // Check the copy out.
  await page.getByRole('link', { name: 'Circulation', exact: true }).click();
  await page.getByLabel(/^Barcode/).fill(barcode);
  await page.getByLabel(/borrower username/i).fill(uname);
  await page.getByLabel(/loan period/i).fill('14');
  await page.getByRole('button', { name: /check out/i }).click();
  await expect(page.getByRole('cell', { name: barcode })).toBeVisible();

  // Dashboard reflects it.
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();
  for (const label of ['Titles', 'Copies', 'On loan', 'Available', 'Overdue', 'Active borrowers', 'Pending resets']) {
    await expect(page.getByText(label, { exact: true })).toBeVisible();
  }
  // Recent activity lists the checkout.
  await expect(page.getByRole('list', { name: 'Recent activity' }).getByText(/Checked out/).first()).toBeVisible();
});

test('dashboard page has no serious accessibility violations', async ({ page }) => {
  await adminLogin(page);
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();
  const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
  const serious = results.violations.filter((v) => ['serious', 'critical'].includes(v.impact ?? ''));
  expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
});
