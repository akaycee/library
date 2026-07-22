import { defineConfig, devices } from '@playwright/test';

// End-to-end tests drive a real browser against the single-process app
// (FastAPI serving the built SPA + API). The web server is started by serve.mjs,
// which builds the frontend, seeds a fresh test database with a known admin, and
// runs uvicorn on port 8123.
const BASE_URL = 'http://127.0.0.1:8123';

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 7_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'node serve.mjs',
    url: `${BASE_URL}/healthz`,
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
