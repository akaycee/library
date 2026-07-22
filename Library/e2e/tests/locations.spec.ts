import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

async function adminLogin(page: Page) {
  await page.goto('/login');
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('Admin12345');
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.getByRole('link', { name: 'Locations', exact: true }).click();
  await expect(page).toHaveURL(/\/locations$/);
}

async function addLocation(page: Page, name: string, typeLabel?: string) {
  const dlg = page.getByRole('dialog');
  await dlg.getByLabel(/^Name/).fill(name);
  if (typeLabel) await dlg.getByLabel(/type label/i).fill(typeLabel);
  await dlg.getByRole('button', { name: /^save$/i }).click();
}

test('staff builds a Room → Shelf → Row structure', async ({ page }) => {
  await adminLogin(page);

  await page.getByRole('button', { name: /add location/i }).click();
  await addLocation(page, 'Main Room', 'Room');
  await expect(page.getByRole('treeitem', { name: 'Main Room' })).toBeVisible();

  // Add a shelf under the room
  await page.getByRole('button', { name: /add sub-location under Main Room/i }).click();
  await addLocation(page, 'Shelf A', 'Shelf');
  await expect(page.getByRole('treeitem', { name: 'Shelf A' })).toBeVisible();

  // Add a row under the shelf
  await page.getByRole('button', { name: /add sub-location under Shelf A/i }).click();
  await addLocation(page, 'Row 1');
  await expect(page.getByRole('treeitem', { name: 'Row 1' })).toBeVisible();
});

test('staff renames and moves a location', async ({ page }) => {
  await adminLogin(page);
  await page.getByRole('button', { name: /add location/i }).click();
  await addLocation(page, 'Storage');
  await page.getByRole('button', { name: /add location/i }).click();
  await addLocation(page, 'Archive');

  // Rename Storage -> Store Room
  await page.getByRole('button', { name: /rename Storage/i }).click();
  const dlg = page.getByRole('dialog');
  await dlg.getByLabel(/^Name/).fill('Store Room');
  await dlg.getByRole('button', { name: /^save$/i }).click();
  await expect(page.getByRole('treeitem', { name: 'Store Room' })).toBeVisible();

  // Move Store Room under Archive
  await page.getByRole('button', { name: /move Store Room/i }).click();
  await page.getByLabel(/new parent/i).click();
  await page.getByRole('option', { name: /Archive/ }).click();
  await page.getByRole('button', { name: /^move$/i }).click();
  // Archive now has a child; expand it and confirm
  await page.getByRole('button', { name: /expand Archive/i }).click();
  await expect(page.getByRole('treeitem', { name: 'Store Room' })).toBeVisible();
});

test('deletion is blocked for non-empty and allowed for empty locations', async ({ page }) => {
  await adminLogin(page);
  await page.getByRole('button', { name: /add location/i }).click();
  await addLocation(page, 'Parent');
  await page.getByRole('button', { name: /add sub-location under Parent/i }).click();
  await addLocation(page, 'Child');

  // Deleting Parent is blocked (has a child)
  await page.getByRole('button', { name: /delete Parent/i }).click();
  await page.getByRole('button', { name: /^delete$/i }).click();
  await expect(page.getByRole('alert')).toContainText(/sub-locations/i);
  await page.getByRole('button', { name: /cancel/i }).click();

  // Delete the empty child (Parent is already expanded, so Child is visible)
  await page.getByRole('button', { name: /delete Child/i }).click();
  await page.getByRole('button', { name: /^delete$/i }).click();
  await expect(page.getByRole('treeitem', { name: 'Child' })).toHaveCount(0);
});

test('locations page has no serious accessibility violations', async ({ page }) => {
  await adminLogin(page);
  const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
  const serious = results.violations.filter((v) => ['serious', 'critical'].includes(v.impact ?? ''));
  expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
});
