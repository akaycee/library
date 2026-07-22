import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// Automated accessibility checks (a subset of WCAG 2.1 AA). These complement,
// but do not replace, the manual accessibility review the spec requires.
for (const path of ['/login', '/signup']) {
  test(`no serious/critical accessibility violations on ${path}`, async ({ page }) => {
    await page.goto(path);
    const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
    const serious = results.violations.filter((v) =>
      ['serious', 'critical'].includes(v.impact ?? ''),
    );
    expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
  });
}
