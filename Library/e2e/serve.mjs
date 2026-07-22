// Test server orchestrator for the E2E suite.
// 1. Builds the frontend into backend/src/static
// 2. Prepares a fresh, isolated test database with a known bootstrap admin
// 3. Runs the single-process FastAPI server on port 8123
//
// Playwright starts this via webServer.command and waits for /healthz.

import { spawn, spawnSync } from 'node:child_process';
import { existsSync, rmSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const backend = resolve(here, '..', 'backend');
const frontend = resolve(here, '..', 'frontend');
const python =
  process.platform === 'win32'
    ? resolve(backend, '.venv', 'Scripts', 'python.exe')
    : resolve(backend, '.venv', 'bin', 'python');
const dbPath = resolve(here, 'test.db');

const env = {
  ...process.env,
  LIBRARY_COOKIE_SECURE: 'false', // tests run over http on loopback
  LIBRARY_REQUIRE_ENCRYPTION: 'false', // plaintext SQLite is fine for the test DB
  LIBRARY_DB_PATH: dbPath, // isolated test DB
  LIBRARY_BOOTSTRAP_PASSWORD: 'Admin12345', // deterministic admin for tests
};

function fail(msg, code) {
  console.error(`[serve] ${msg}`);
  process.exit(code ?? 1);
}

// 1. Build the frontend (so the server serves the current UI).
console.log('[serve] Building frontend...');
const build = spawnSync('npm', ['run', 'build'], {
  cwd: frontend,
  env: process.env,
  stdio: 'inherit',
  shell: true,
});
if (build.status !== 0) fail('frontend build failed', build.status);

// 2. Fresh database.
for (const f of [dbPath, `${dbPath}-wal`, `${dbPath}-shm`]) {
  if (existsSync(f)) rmSync(f);
}

function pyRun(args, label) {
  const r = spawnSync(python, args, { cwd: backend, env, stdio: 'inherit' });
  if (r.status !== 0) fail(`${label} failed`, r.status);
}
console.log('[serve] Creating schema + bootstrap admin...');
pyRun(['-m', 'src.core.schema_init'], 'schema_init');
pyRun(['-m', 'src.core.setup'], 'setup');
// For tests, the seeded admin should be immediately usable (skip forced change).
pyRun(
  [
    '-c',
    "from src.core.db import SessionLocal; from src.models.user import User; from sqlalchemy import select; db=SessionLocal(); u=db.scalar(select(User).where(User.username_normalized=='admin')); u.force_password_change=False; db.commit(); db.close()",
  ],
  'clear-force-change',
);

// 3. Run the server (stays in foreground so Playwright can manage it).
console.log('[serve] Starting server on http://127.0.0.1:8123 ...');
const server = spawn(
  python,
  ['-m', 'uvicorn', 'src.main:app', '--host', '127.0.0.1', '--port', '8123'],
  { cwd: backend, env, stdio: 'inherit' },
);
server.on('exit', (code) => process.exit(code ?? 0));
process.on('SIGTERM', () => server.kill());
process.on('SIGINT', () => server.kill());
