import { test, expect, type Page } from '@playwright/test';

async function signUp(page: Page, username: string, password = 'abcd1234') {
  await page.goto('/signup');
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: /create account/i }).click();
}

test('borrower can sign up and reach the home view', async ({ page }) => {
  const username = `borrower_${Date.now()}`;
  await signUp(page, username);
  await expect(page.getByText(/signed in as borrower/i)).toBeVisible();
  await expect(page.getByText(new RegExp(`Welcome, ${username}`, 'i'))).toBeVisible();
});

test('logout returns to login and guards the home route', async ({ page }) => {
  await signUp(page, `borrower_${Date.now()}`);
  await expect(page.getByText(/signed in as borrower/i)).toBeVisible();

  await page.getByRole('button', { name: /log out/i }).click();
  await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();

  await page.goto('/');
  await expect(page).toHaveURL(/\/login$/);
});

test('login shows a friendly, indistinguishable error on wrong credentials', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Username').fill('does-not-exist');
  await page.getByLabel('Password').fill('wrongpass1');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page.getByRole('alert')).toContainText(/incorrect username or password/i);
});

test('sign up rejects a weak password with a clear message', async ({ page }) => {
  await page.goto('/signup');
  await page.getByLabel('Username').fill(`weak_${Date.now()}`);
  await page.getByLabel('Password').fill('weak');
  await page.getByRole('button', { name: /create account/i }).click();
  await expect(page.getByRole('alert')).toContainText(/at least 8 characters/i);
});
