import { test, expect, type Page } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:8123';

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

test('admin can create a librarian and see it in the list', async ({ page }) => {
  await adminLogin(page);
  await gotoViaMore(page, /manage users/i);
  await expect(page).toHaveURL(/\/users$/);

  const username = `libby_${Date.now()}`;
  await page.getByRole('button', { name: /add user/i }).click();
  await page.getByLabel('Username').fill(username);
  await page.getByLabel(/temporary password/i).fill('abcd1234');
  // Default role in the dialog is "librarian".
  await page.getByRole('button', { name: /^create$/i }).click();

  await expect(page.getByRole('cell', { name: username, exact: true })).toBeVisible();
});

test('a borrower cannot see or reach user management', async ({ page }) => {
  const username = `borrower_${Date.now()}`;
  await page.goto('/signup');
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Password').fill('abcd1234');
  await page.getByRole('button', { name: /create account/i }).click();
  await expect(page.getByText(/signed in as borrower/i)).toBeVisible();

  await expect(page.getByRole('link', { name: /manage users/i })).toHaveCount(0);

  // Direct navigation is guarded and redirects to home.
  await page.goto('/users');
  await expect(page).toHaveURL(/:8123\/$/);
});

test('deactivating a user revokes their active session', async ({ browser }) => {
  const adminCtx = await browser.newContext({ baseURL: BASE_URL });
  const userCtx = await browser.newContext({ baseURL: BASE_URL });
  const admin = await adminCtx.newPage();
  const user = await userCtx.newPage();
  const username = `victim_${Date.now()}`;

  // The user self-registers and is signed in.
  await user.goto('/signup');
  await user.getByLabel('Username').fill(username);
  await user.getByLabel('Password').fill('abcd1234');
  await user.getByRole('button', { name: /create account/i }).click();
  await expect(user.getByText(/signed in as borrower/i)).toBeVisible();

  // The admin deactivates that user.
  await adminLogin(admin);
  await gotoViaMore(admin, /manage users/i);
  const row = admin.getByRole('row', { name: new RegExp(username) });
  await row.getByRole('button', { name: /deactivate/i }).click();
  await expect(row.getByText('deactivated')).toBeVisible();

  // The user's session is now revoked: a reload bounces them to login.
  await user.reload();
  await expect(user).toHaveURL(/\/login$/);

  await adminCtx.close();
  await userCtx.close();
});
