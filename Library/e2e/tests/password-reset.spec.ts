import { test, expect } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:8123';

test('full email-free password reset flow', async ({ browser }) => {
  const adminCtx = await browser.newContext({ baseURL: BASE_URL });
  const userCtx = await browser.newContext({ baseURL: BASE_URL });
  const admin = await adminCtx.newPage();
  const user = await userCtx.newPage();
  const username = `reset_${Date.now()}`;

  // The user self-registers, then logs out.
  await user.goto('/signup');
  await user.getByLabel('Username').fill(username);
  await user.getByLabel('Password').fill('abcd1234');
  await user.getByRole('button', { name: /create account/i }).click();
  await expect(user.getByText(/signed in as borrower/i)).toBeVisible();
  await user.getByRole('button', { name: /log out/i }).click();

  // The user requests a password reset.
  await user.goto('/forgot-password');
  await user.getByLabel('Username').first().fill(username);
  await user.getByRole('button', { name: /request reset/i }).click();
  await expect(user.getByText(/an administrator has been notified/i)).toBeVisible();

  // The admin issues a temporary password and captures it.
  await admin.goto('/login');
  await admin.getByLabel('Username').fill('admin');
  await admin.getByLabel('Password').fill('Admin12345');
  await admin.getByRole('button', { name: /sign in/i }).click();
  await admin.getByRole('button', { name: /^more$/i }).click();
  await admin.getByRole('menuitem', { name: /password resets/i }).click();
  await expect(admin).toHaveURL(/\/reset-queue$/);
  const row = admin.getByRole('row', { name: new RegExp(username) });
  await row.getByRole('button', { name: /issue temporary password/i }).click();
  const tempPassword = (await admin.getByTestId('temp-password').innerText()).trim();
  expect(tempPassword.length).toBeGreaterThan(6);
  await admin.getByRole('button', { name: /^done$/i }).click();

  // The user signs in with the temporary password and is forced to change it.
  await user.goto('/forgot-password');
  // Step 2 form is the second Username field on the page.
  await user.getByLabel('Username').nth(1).fill(username);
  await user.getByLabel(/temporary password/i).fill(tempPassword);
  await user.getByRole('button', { name: /continue/i }).click();

  await expect(user).toHaveURL(/\/force-change$/);
  await user.getByLabel(/^new password/i).fill('brandnew12');
  await user.getByLabel(/confirm new password/i).fill('brandnew12');
  await user.getByRole('button', { name: /save new password/i }).click();

  // Lands on home, signed in with the new full session.
  await expect(user.getByText(/signed in as borrower/i)).toBeVisible();

  // The new password works on a fresh login; the old one does not.
  await user.getByRole('button', { name: /log out/i }).click();
  await user.goto('/login');
  await user.getByLabel('Username').fill(username);
  await user.getByLabel('Password').fill('abcd1234');
  await user.getByRole('button', { name: /sign in/i }).click();
  await expect(user.getByRole('alert')).toContainText(/incorrect username or password/i);

  await user.getByLabel('Username').fill(username);
  await user.getByLabel('Password').fill('brandnew12');
  await user.getByRole('button', { name: /sign in/i }).click();
  await expect(user.getByText(/signed in as borrower/i)).toBeVisible();

  await adminCtx.close();
  await userCtx.close();
});
