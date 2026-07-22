# Implementation Plan: Authentication, Roles & User Management

**Branch**: `001-auth-user-management` | **Date**: 2026-07-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-auth-user-management/spec.md`

## Summary

Deliver the foundational authentication, three-role authorization (Administrator,
Librarian, Borrower), user management, and an email-free password-reset workflow
(Administrator-issued one-time temporary password). The implementation targets a
**local-first, single-machine deployment** for a small school library,
prioritizing low cost, low maintenance, and ease of use for non-technical
librarians, while keeping a clean path to a later cloud migration.

The chosen approach is a lightweight web application deployed as a **single
FastAPI process** that serves both the documented, versioned JSON API and the
compiled React frontend as static files over **HTTPS**. The backend is backed by
**SQLite** (through SQLAlchemy); the **React + Vite + MUI** frontend provides
accessible Material Design foundations that are verified against WCAG 2.1 AA.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x / Node 20+ (frontend)

**Primary Dependencies**: FastAPI, Uvicorn, SQLAlchemy 2.x, Pydantic v2, Passlib[argon2], Alembic (migrations), SQLCipher (encrypted-at-rest SQLite, e.g., sqlcipher3); React 18, Vite, MUI (Material UI) v5, React Router; axe-core (accessibility testing)

**Storage**: SQLite encrypted at rest via **SQLCipher** (local file) through SQLAlchemy for v1; migration to PostgreSQL for the cloud phase is a tested migration project (enum/collation/timestamp/UUID differences), not a connection-string swap

**Testing**: pytest + httpx (backend), Vitest + React Testing Library (frontend), Playwright + axe (end-to-end & accessibility)

**Target Platform**: Local desktop/server (Windows/Linux), single instance served over HTTPS, bound to an explicit LAN interface; accessed through a web browser on the LAN

**Project Type**: Web application (single FastAPI process serving API + compiled frontend)

**Performance Goals**: Interactive UI actions feel instant at library scale; auth and user-management API calls well under the constitution's 500ms catalog-query budget

**Constraints**: No email/external services in v1; must run fully offline/local; database encrypted at rest (SQLCipher) with a startup-provided key; served over HTTPS so Secure cookies are honored and data is protected in transit; data and schema migration to the cloud is tested, not assumed; WCAG 2.1 AA verified via axe + keyboard journeys + manual checklist; passwords stored only as Argon2id hashes

**Scale/Scope**: Small — on the order of hundreds of items and dozens to low-hundreds of user accounts; a handful of concurrent users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Data Integrity First**: PASS — account and role mutations run inside DB transactions; reset issuance is atomic; no partial states.
- **II. Complete Audit Trail**: PASS — account creation, role changes, deactivations, reset requests, and temp-password issuance are logged append-only with who/what/when; accounts are soft-deleted.
- **III. Role-Based Access Control**: PASS — exactly the three roles are enforced; self-registration limited to Borrower; last-Administrator protection; bootstrap admin provisioned by an idempotent setup command; every authorization check rejects revoked/expired sessions and deactivated users.
- **IV. API-First Design**: PASS — every capability is exposed via the FastAPI JSON API (auto-generated, versioned OpenAPI) before the UI consumes it; schemas validated with Pydantic; state-changing endpoints are CSRF-protected.
- **V. Test-First**: PASS — pytest/Vitest suites written before implementation; ≥80% coverage target; **Playwright end-to-end tests** cover register→login→logout and the full reset flow through a real browser (validating session cookies, rotation, CSRF, and the forced-password-change gate).
- **VI. Ease of Use**: PASS — MUI provides accessible Material Design foundations; WCAG 2.1 AA is verified with automated axe checks, explicit Playwright keyboard journeys, and a manual review checklist; role-aware navigation.
- **VII. Lightweight & Low-Maintenance**: PASS — a single FastAPI process serves both the API and the compiled frontend, so there is one thing to start and maintain, no CORS, and same-origin cookies; SQLCipher keeps the encrypted store self-contained with no separate DB server.
- **Additional constraints**: PASS — local-only encrypted SQLite (SQLCipher) with provider-agnostic ORM; PII protected at rest (SQLCipher) and in transit (HTTPS); no email dependency.

No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-auth-user-management/
├── plan.md              # This file
├── research.md          # Phase 0 output — stack decisions & alternatives
├── data-model.md        # Phase 1 output — entities & relationships
├── quickstart.md        # Phase 1 output — how to run locally
├── contracts/           # Phase 1 output — API contract
│   └── auth-api.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (from specify)
└── tasks.md             # Created later by /speckit.tasks (NOT here)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/          # SQLAlchemy models: User, Session, PasswordResetRequest, TemporaryPasswordGrant, AuditLogEntry
│   ├── schemas/         # Pydantic request/response schemas
│   ├── services/        # auth, sessions, users, roles, password-reset, audit logic
│   ├── api/             # FastAPI routers (versioned under /api/v1)
│   ├── core/            # config, security (hashing/sessions/CSRF), db session, seeding/setup
│   ├── static/          # compiled frontend (Vite build output) served by FastAPI
│   └── main.py          # app entrypoint — serves /api/v1 + static SPA
├── migrations/          # Alembic migrations
└── tests/
    ├── integration/
    └── unit/

frontend/
├── src/
│   ├── components/      # shared MUI components (forms, layout, nav)
│   ├── pages/           # SignUp, Login, Users, ResetQueue, ForceChangePassword
│   ├── services/        # API client
│   └── auth/            # session/context, route guards
└── tests/

e2e/
└── tests/              # Playwright end-to-end specs (register/login/logout, reset flow)
```

**Structure Decision**: Web application deployed as a **single FastAPI process**.
During development the Vite dev server runs for hot-reload; for the packaged/local
deployment the frontend is built to static files that FastAPI serves alongside the
versioned `/api/v1` API. This enforces the API-first principle (the UI talks only
to the versioned API), keeps the backend independently testable and
cloud-portable, and satisfies the Lightweight & Low-Maintenance principle
(one process, no CORS, same-origin cookies).

## Complexity Tracking

No constitution violations — section intentionally empty.
