import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const BASE = 'http://127.0.0.1:8123';

async function adminLogin(page: Page) {
  await page.goto('/login');
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('Admin12345');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page.getByRole('link', { name: 'Circulation', exact: true })).toBeVisible();
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

test('staff checks out a copy and returns it; borrower sees it', async ({ page, browser }) => {
  // Borrower self-registers in a separate context.
  const ctx = await browser.newContext({ baseURL: BASE });
  const borrower = await ctx.newPage();
  const uname = `bor_${Date.now()}`;
  await borrower.goto('/signup');
  await borrower.getByLabel('Username').fill(uname);
  await borrower.getByLabel('Password').fill('abcd1234');
  await borrower.getByRole('button', { name: /create account/i }).click();
  await expect(borrower.getByText(/signed in as borrower/i)).toBeVisible();

  // Admin sets up a copy and checks it out.
  const titleName = `Circ Book ${Date.now()}`;
  await adminLogin(page);
  const barcode = await seedCopy(page, titleName, `Circ Loc ${Date.now()}`);

  await page.getByRole('link', { name: 'Circulation', exact: true }).click();
  await page.getByLabel(/^Barcode/).fill(barcode);
  await page.getByLabel(/borrower username/i).fill(uname);
  await page.getByLabel(/loan period/i).fill('14');
  await page.getByRole('button', { name: /check out/i }).click();
  await expect(page.getByRole('cell', { name: barcode })).toBeVisible();

  // Borrower sees the loan in My loans.
  await borrower.getByRole('link', { name: 'My loans', exact: true }).click();
  await expect(borrower.getByText(new RegExp(titleName))).toBeVisible();

  // Return it.
  await page.getByRole('button', { name: /^return$/i }).click();
  await expect(page.getByText(/no active loans/i)).toBeVisible();

  await ctx.close();
});

test('circulation page has no serious accessibility violations', async ({ page }) => {
  await adminLogin(page);
  await page.getByRole('link', { name: 'Circulation', exact: true }).click();
  const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
  const serious = results.violations.filter((v) => ['serious', 'critical'].includes(v.impact ?? ''));
  expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
});

test('unknown borrower can be quick-created at the desk and checked out', async ({ page }) => {
  const titleName = `QC Book ${Date.now()}`;
  await adminLogin(page);
  const barcode = await seedCopy(page, titleName, `QC Loc ${Date.now()}`);

  const newBorrower = `qc_${Date.now()}`;
  await page.getByRole('link', { name: 'Circulation', exact: true }).click();
  await page.getByLabel(/^Barcode/).fill(barcode);
  await page.getByLabel(/borrower username/i).fill(newBorrower);
  await page.getByLabel(/loan period/i).fill('7');
  await page.getByRole('button', { name: /check out/i }).click();

  // The quick-create dialog appears; keep the generated-password option.
  const dlg = page.getByRole('dialog');
  await expect(dlg).toBeVisible();
  await dlg.getByRole('button', { name: /create & check out/i }).click();

  // Success notice reveals a temporary password, and the loan is now active.
  await expect(page.getByText(/temporary password:/i)).toBeVisible();
  await expect(page.getByRole('cell', { name: barcode })).toBeVisible();
  await expect(page.getByRole('cell', { name: newBorrower })).toBeVisible();
});

