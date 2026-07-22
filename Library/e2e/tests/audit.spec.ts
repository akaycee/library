import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

async function adminLogin(page: Page) {
  await page.goto('/login');
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('Admin12345');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page.getByRole('button', { name: /^more$/i })).toBeVisible();
}

/** Navigates to a destination that lives under the "More" overflow menu. */
async function gotoViaMore(page: Page, name: RegExp | string) {
  await page.getByRole('button', { name: /^more$/i }).click();
  await page.getByRole('menuitem', { name }).click();
}

/** Creates a title so there's a fresh, attributable audit entry. */
async function createTitle(page: Page, titleName: string) {
  await page.getByRole('link', { name: 'Catalog', exact: true }).click();
  await page.getByRole('button', { name: /add title/i }).click();
  const dlg = page.getByRole('dialog');
  await dlg.getByLabel(/^Title/).fill(titleName);
  await dlg.getByRole('button', { name: /^save$/i }).click();
  await expect(page.getByRole('link', { name: titleName })).toBeVisible();
}

test('staff can review and filter the audit trail', async ({ page }) => {
  await adminLogin(page);
  const titleName = `Audit Book ${Date.now()}`;
  await createTitle(page, titleName);

  await gotoViaMore(page, 'Audit');
  await expect(page.getByRole('heading', { name: /audit trail/i })).toBeVisible();

  // There are entries, and the admin appears as an actor.
  await expect(page.getByRole('cell', { name: 'admin' }).first()).toBeVisible();

  // Filter by the title.create action: every visible action chip should match.
  await page.getByLabel('Action').click();
  await page.getByRole('option', { name: 'title.create' }).click();
  await expect(page.getByText('title.create').first()).toBeVisible();
  const otherActions = page.getByText(/^loan\.|^location\.|^copy\./);
  await expect(otherActions).toHaveCount(0);

  // Searching a username that matches nobody yields the empty state.
  await page.getByLabel(/user \(actor or target\)/i).fill(`nobody_${Date.now()}`);
  await expect(page.getByText(/no matching audit entries/i)).toBeVisible();
});

test('audit page has no serious accessibility violations', async ({ page }) => {
  await adminLogin(page);
  await gotoViaMore(page, 'Audit');
  await expect(page.getByRole('heading', { name: /audit trail/i })).toBeVisible();
  const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
  const serious = results.violations.filter((v) => ['serious', 'critical'].includes(v.impact ?? ''));
  expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
});

test('a borrower cannot reach the audit trail', async ({ page, browser }) => {
  // Register a borrower in a fresh context.
  const ctx = await browser.newContext();
  const borrower = await ctx.newPage();
  const uname = `aud_bor_${Date.now()}`;
  await borrower.goto('/signup');
  await borrower.getByLabel('Username').fill(uname);
  await borrower.getByLabel('Password').fill('abcd1234');
  await borrower.getByRole('button', { name: /create account/i }).click();
  await expect(borrower.getByText(/signed in as borrower/i)).toBeVisible();

  // No Audit link, and direct navigation is redirected away.
  await expect(borrower.getByRole('link', { name: 'Audit', exact: true })).toHaveCount(0);
  await borrower.goto('/audit');
  await expect(borrower.getByRole('heading', { name: /audit trail/i })).toHaveCount(0);

  await ctx.close();
});
