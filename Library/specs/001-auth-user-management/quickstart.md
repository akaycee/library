# Quickstart: Authentication, Roles & User Management

**Feature**: Authentication, Roles & User Management
**Audience**: Developers running the app locally (v1 is local-only).

## Prerequisites

- Python 3.11+
- Node.js 20+
- No database server required — v1 uses a local SQLite file **encrypted at rest**
  with SQLCipher. Set a database encryption key before running:

```powershell
$env:LIBRARY_DB_KEY = "<a-strong-secret>"   # required to open the encrypted DB; never commit this
```

> Losing `LIBRARY_DB_KEY` means the database cannot be opened — back it up securely.

## Layout

```text
backend/    # FastAPI + SQLAlchemy + SQLite
frontend/   # React + Vite + MUI
```

## Backend — first run

## Development mode (hot-reload)

Run the backend and the Vite dev server side by side while coding.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head          # create the SQLite schema
python -m src.core.setup      # idempotent bootstrap Administrator setup (see below)
uvicorn src.main:app --reload # API at http://127.0.0.1:8000 (dev-only HTTP)
```

- API docs (auto-generated OpenAPI): http://127.0.0.1:8000/docs
- **Bootstrap setup** (`src.core.setup`) is idempotent and safe:
  - Creates the Administrator **only when no users exist**, in a single transaction.
  - Prompts for a password interactively, or generates a random one **shown once**;
    it refuses default/well-known credentials and never writes the password to logs.
  - Re-running it when any user already exists makes no changes.
  - The account is created with `force_password_change = true`.
- Dev mode binds to `127.0.0.1` over plain HTTP and uses **non-Secure** cookies
  strictly for local development.

```powershell
cd frontend
npm install
npm run dev                   # UI (Vite hot-reload) at http://127.0.0.1:5173
```

The frontend talks only to the backend API under `/api/v1`.

## Packaged / local deployment (single process)

Build the frontend to static files and let the **single FastAPI process** serve
both the API and the UI — one thing to start and maintain, no CORS, same-origin
cookies.

```powershell
cd frontend
npm run build                 # outputs static files into backend/src/static

cd ..\backend
.\.venv\Scripts\Activate.ps1
# Serve over HTTPS, bound to an explicit LAN interface so LAN clients can reach it
# and Secure cookies are honored. Provide a local TLS cert/key.
uvicorn src.main:app --host 0.0.0.0 --port 8443 `
  --ssl-certfile .\certs\localhost.pem --ssl-keyfile .\certs\localhost-key.pem
```

Open `https://<this-machine-lan-ip>:8443` — the API lives under `/api/v1` and the
UI is served from the same origin. Cookies are `Secure`, so HTTPS is required for
LAN use; plain HTTP is available only in dev mode on `127.0.0.1`.

> Generate a local development certificate with a tool such as `mkcert`
> (`mkcert localhost <lan-ip>`), or supply your own cert/key.

## Smoke test (manual)

1. Open the UI, register a new Borrower, then log out and log back in.
2. Log in as the bootstrap Administrator, change the temporary password.
3. As Administrator, create a Librarian account and confirm it appears in the user list.
4. From the login page, request a password reset for a user; as Administrator,
   issue a temporary password; sign in as that user and set a new password.

## Running tests

```powershell
# Backend
cd backend
.\.venv\Scripts\Activate.ps1
pytest --cov=src

# Frontend
cd frontend
npm test

# End-to-end (Playwright)
cd e2e
npm install
npx playwright install        # one-time browser download
npx playwright test
```

Target ≥80% coverage (per constitution). Integration and Playwright E2E tests must
cover register→login→logout and the full password-reset flow.

## Cloud migration note (later phase)

Moving to PostgreSQL is a **tested migration project**, not a connection-string
swap. SQLite and PostgreSQL differ in enum storage, case/collation, timestamp
timezone handling, and UUID types. The migration is covered by tests that:

- run the full Alembic migration set against a PostgreSQL instance,
- verify `username_normalized` uniqueness behaves identically, and
- validate data round-trips (timestamps in UTC, enums, IDs).

Only after those tests pass is the connection string switched and
`alembic upgrade head` run against the cloud database.
