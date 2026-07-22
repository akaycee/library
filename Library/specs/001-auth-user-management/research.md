# Phase 0 Research: Lightweight Stack for a Local School Library

**Feature**: Authentication, Roles & User Management
**Date**: 2026-07-19

## Context & Constraints

- Deployment is **local-first** on a single machine, later moved to the cloud.
- Operated by **non-technical, older librarians** — ease of use and low
  maintenance are paramount.
- Small scale: hundreds of items, dozens to low-hundreds of accounts, a few
  concurrent users.
- Constitution mandates: API-first, Material Design + WCAG 2.1 AA, test-first,
  audit trail, no hard cloud dependencies, and **no email in v1**.
- Priority: the **most lightweight** approach that still satisfies the above.

## Decision 1 — Backend framework: FastAPI (Python)

**Decision**: Use FastAPI with Uvicorn.

**Rationale**:
- Generates a **documented, versioned OpenAPI** automatically, directly
  satisfying the API-first principle with near-zero extra effort.
- Pydantic v2 gives boundary schema validation (rejects invalid payloads) for free.
- Python was already selected as the project script language (`init-options.json`),
  keeping the toolchain consistent.
- Small dependency footprint; single-process, easy to run locally with one command.

**Alternatives considered**:
- *Node/Express*: viable but requires more manual wiring for schema validation and
  API docs.
- *Django*: batteries-included but heavier than needed for this scope; more to learn
  and maintain.
- *Flask*: lighter but lacks FastAPI's built-in validation and OpenAPI generation.

## Decision 2 — Database: SQLite via SQLAlchemy, encrypted at rest with SQLCipher (migrate to Postgres later)

**Decision**: SQLite file database in v1, **encrypted at rest using SQLCipher**,
accessed through SQLAlchemy 2.x ORM, with Alembic migrations. The encryption key
is supplied at startup via configuration/environment.

**Rationale**:
- **Zero configuration** — no separate database server to install or maintain,
  ideal for a local, non-technical environment.
- The whole database is a single (encrypted) file: trivial to back up and hand off.
- **SQLCipher** provides transparent AES encryption at rest, satisfying the
  constitution's "PII MUST be encrypted at rest" mandate while staying a
  self-contained, zero-server store (consistent with Principle VII).
- Using SQLAlchemy (and avoiding SQLite-specific SQL) keeps the models close to
  portable, but the move to **PostgreSQL is a tested migration project**, not a
  connection-string swap: enum storage, case/collation, timestamp timezone, and
  UUID types differ and must be verified by migration tests.
- Alembic gives reversible, reviewable migrations (per the development workflow).

**Key handling**: the SQLCipher key is provided at startup, never committed to
source control and never written to logs; losing the key means losing the data,
so backup/rotation of the key is documented operationally.

**Alternatives considered**:
- *PostgreSQL now*: unnecessary operational weight for a local single-user-ish
  deployment; deferred to the cloud phase.
- *Raw SQLite / no ORM*: lighter but would couple the code to SQLite and complicate
  the future migration.

## Decision 3 — Frontend: React + Vite + MUI (Material UI)

**Decision**: React (TypeScript) built with Vite, using MUI components.

**Rationale**:
- MUI is a mature **Material Design** implementation that provides **accessible
  foundations** (contrast-aware theming, keyboard-navigable components, focus
  management). It does not by itself make the app WCAG 2.1 AA compliant —
  conformance is verified with automated axe checks plus explicit keyboard
  journeys and a manual review checklist (focus order/visibility, dialogs, error
  messaging, labels, contrast).
- Vite is a fast, lightweight build/dev tool.
- Decoupled SPA reinforces API-first: the UI consumes only the versioned API.

**Alternatives considered**:
- *Server-rendered templates (Jinja2) + a Material CSS kit*: fewer moving parts and
  no JS build, but accessibility and Material fidelity would be more manual and
  harder to guarantee to AA. Rejected because the constitution makes Material +
  accessibility non-negotiable, and MUI delivers them reliably.
- *Angular/Vue*: comparable capability; React + MUI chosen for ubiquity and the
  breadth of accessible ready-made components.

## Decision 4 — Authentication mechanism: server-side sessions + Argon2

**Decision**: Server-side sessions. The auth cookie carries only an opaque random
token (`HttpOnly`, `Secure`, `SameSite=Strict`); the server stores only the
token's hash in a `Session` table with absolute expiry and idle timeout. Sessions
are **rotated** on login and password change, **revoked** on logout, and every
authorization check rejects expired/revoked/idle sessions and deactivated users.
Completing a password reset revokes all of a user's sessions. Passwords are hashed
with Argon2id via Passlib. State-changing requests are **CSRF-protected** via a
double-submit token plus trusted-origin validation.

**Rationale**:
- For a single local instance, server-side sessions are **simpler and safer** than
  JWT (true logout, easy revocation on deactivation/reset, no token-leak window).
- Storing only the token hash means a database read cannot reveal live credentials.
- Rotation prevents session fixation; SameSite + CSRF token + origin checks give
  layered CSRF defense (SameSite alone is insufficient across same-site hosts).
- Argon2id is a current best-practice password hash.
- Meets FR-003, FR-005, FR-006, FR-007a–c, FR-024.

**Alternatives considered**:
- *JWT access/refresh tokens*: more moving parts and revocation complexity, with no
  benefit at this scale.

## Decision 5 — Email-free password reset

**Decision**: Implement the Administrator-issued, one-time, expiring temporary
password workflow entirely inside the app (request queue → issue → forced change),
as specified.

**Rationale**:
- No email or SMS dependency (constitution + user constraint).
- Out-of-band human identity verification is realistic for a single physical library.
- Temporary passwords are single-use and time-boxed, limiting risk.

**Alternatives considered**:
- *Emailed reset links*: rejected outright — email is out of scope for v1.
- *Security questions/PIN*: explicitly deferred by the user for v1.

## Decision 6 — Deployment: single FastAPI process serving API + static frontend

**Decision**: In the packaged/local deployment, one FastAPI process serves both
the versioned `/api/v1` API and the compiled Vite static files. During development,
the Vite dev server runs separately for hot-reload.

**Rationale**:
- **One thing to start and maintain** — satisfies Principle VII (Lightweight &
  Low-Maintenance) and Principle VI (ease of use for non-technical staff).
- **No CORS** and only one port to manage.
- **Same-origin cookies** simplify and harden the session/auth setup.
- Trivially portable to a single container/process in the cloud phase.

**Alternatives considered**:
- *Two long-running processes (separate API + static server)*: more moving parts,
  CORS configuration, and cross-origin cookie handling for no benefit at this scale.

## Decision 7 — Transport & LAN binding: HTTPS on an explicit interface

**Decision**: Serve over **HTTPS** (local TLS certificate) bound to an explicit
LAN interface (e.g., `0.0.0.0` or a specific host IP), not `127.0.0.1`, so LAN
clients can reach it and `Secure` cookies are honored. A **development-only**
mode may bind to `127.0.0.1` over plain HTTP with non-`Secure` cookies.

**Rationale**:
- `Secure` cookies are not reliably sent over plain HTTP, so the earlier
  HTTP-on-LAN description was inconsistent with the cookie policy.
- Binding to `127.0.0.1` is not LAN-accessible; an explicit interface is required.
- A clearly separated dev-only HTTP mode keeps local development frictionless
  without weakening the LAN deployment.

**Alternatives considered**:
- *Plain HTTP on the LAN with non-Secure cookies*: rejected for a
  credential-bearing app, even on a trusted LAN.
- *Reverse proxy for TLS termination*: reasonable later, but adds a component that
  conflicts with the single-process, low-maintenance goal for v1.

## Testing Approach

- **Backend**: pytest + httpx for API/integration tests; unit tests for services.
- **Frontend**: Vitest + React Testing Library for components and flows.
- **End-to-end**: Playwright drives a real browser to verify the core journeys
  (register→login→logout and the full password-reset flow), including session
  cookies, rotation, CSRF, the forced-password-change gate, and keyboard
  navigation; **axe** runs automated accessibility checks alongside a manual
  WCAG 2.1 AA review checklist.
- Test-first per constitution; ≥80% coverage; integration + E2E coverage for the
  register→login→logout and reset flows, plus a tested SQLite→PostgreSQL migration.

## Summary of Choices

| Concern        | Choice                                   |
|----------------|------------------------------------------|
| Backend        | FastAPI + Uvicorn (Python 3.11+)         |
| Data           | SQLite (SQLCipher, encrypted at rest) via SQLAlchemy + Alembic |
| Frontend       | React + Vite + MUI (TypeScript)          |
| Auth           | Server-side sessions (hashed opaque token) + Argon2id + CSRF |
| Reset          | Admin-issued one-time temp password (consumed at login) |
| Tests          | pytest/httpx + Vitest/RTL + Playwright + axe |
| Deployment     | Single FastAPI process (API + static UI) over HTTPS |
| Cloud path     | SQLite → PostgreSQL as a tested migration project |
