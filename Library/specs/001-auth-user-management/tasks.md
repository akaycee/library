---
description: "Task list for Authentication, Roles & User Management"
---

# Tasks: Authentication, Roles & User Management

**Input**: Design documents from `specs/001-auth-user-management/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/auth-api.md

**Tests**: Included and REQUIRED — the constitution mandates Test-First (Principle V). Tests MUST be written and MUST fail before implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story the task belongs to (US1, US2, US3)
- Exact file paths are included in descriptions

## Path Conventions

Web app, single-process deployment (per plan.md):
- Backend: `backend/src/`, `backend/tests/`
- Frontend: `frontend/src/`, `frontend/tests/`
- End-to-end: `e2e/tests/` (Playwright)
- Frontend build output served by FastAPI from `backend/src/static/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create the `backend/` and `frontend/` project structure per plan.md (src subfolders, tests, e2e)
- [x] T002 Initialize backend: Python venv, `backend/requirements.txt` (FastAPI, Uvicorn, SQLAlchemy 2.x, Pydantic v2, Passlib[argon2], Alembic, pytest, httpx)
- [x] T003 [P] Initialize frontend: Vite + React + TypeScript, add MUI, React Router, and Vitest + React Testing Library in `frontend/`
- [x] T004 [P] Initialize Playwright + axe-core in `e2e/` with config targeting the single-process app URL
- [ ] T005 [P] Configure linting/formatting: Ruff + Black for backend, ESLint + Prettier for frontend  _(deferred)_
- [x] T006 Configure Vite build to output to `backend/src/static/` and add a coverage config targeting ≥80%

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Create app config and settings in `backend/src/core/config.py` (encrypted DB path + SQLCipher key from env, session secret, session expiry/idle, throttling params, temp-password expiry, TLS/host, CSRF, password policy)
- [x] T008 Set up SQLAlchemy engine/session (SQLCipher-encrypted, key from config; fail fast if key missing) and declarative base in `backend/src/core/db.py`
- [ ] T008a [P] Test that the database is encrypted at rest (raw file is not readable without the key; correct key opens it) in `backend/tests/integration/test_encryption_at_rest.py`  _(deferred — needs SQLCipher driver installed)_
- [ ] T009 Initialize Alembic in `backend/migrations/` wired to the SQLAlchemy metadata  _(substituted: schema created via `create_all` on startup for v1; Alembic pending)_
- [x] T010 [P] Implement Argon2id password hashing + verification helpers in `backend/src/core/security.py`
- [x] T011 [P] Implement server-side session store + middleware: opaque token, hashed storage, absolute expiry + idle timeout, rotation, and revocation, in `backend/src/core/security.py` and `backend/src/services/sessions.py`
- [x] T011a [P] Implement CSRF protection (double-submit token + trusted-origin/Fetch-Metadata validation) as middleware/dependency in `backend/src/core/security.py`
- [x] T011b [P] Implement progressive login throttling keyed by account + client/IP (bounded lock, self-recovery) in `backend/src/services/throttle.py`
- [x] T012 Create the `Session` model in `backend/src/models/session.py` and the `AuditLogEntry` model (append-only, with `reason`/`detail` for the constitution's "why") in `backend/src/models/audit.py`, plus an audit service in `backend/src/services/audit.py`
- [x] T013 Implement role-based authorization dependencies/guards (Administrator/Librarian/Borrower) that also reject expired/revoked/idle sessions and deactivated users, in `backend/src/api/deps.py`
- [x] T014 Set up FastAPI app with versioned `/api/v1` router, error handling, CSRF, static-file serving of `backend/src/static/` (+ SPA fallback), and HTTPS/explicit-host serving (dev-only HTTP on 127.0.0.1) in `backend/src/main.py`
- [x] T015 Implement the **idempotent bootstrap setup command** in `backend/src/core/setup.py` (creates Administrator only when no users exist, transactional; prompts or generates a one-time password shown once; refuses defaults; never logs the password; force_password_change=true)
- [x] T016 [P] Frontend app shell: MUI theme, router, API client (with CSRF header handling), and session/auth context + route guards in `frontend/src/auth/` and `frontend/src/services/`

**Checkpoint**: Foundation ready — user stories can now begin

---

## Phase 3: User Story 1 — Borrower self-registration and login (Priority: P1) 🎯 MVP

**Goal**: A visitor can register a Borrower account, log in, and log out.

**Independent Test**: Register a new borrower, log out, log back in with those credentials.

### Tests for User Story 1 ⚠️ (write first, must fail)

- [x] T017 [P] [US1] Contract tests for `POST /api/v1/auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` in `backend/tests/integration/test_auth_contract.py`
- [x] T018 [P] [US1] Integration test for register→login→logout journey, including session rotation on login and revocation on logout, in `backend/tests/integration/test_auth_flow.py`
- [x] T019 [P] [US1] Unit tests for password hashing, session store, CSRF, and progressive throttling (incl. concurrent attempts and account+client keying) in `backend/tests/unit/test_security.py`
- [x] T019a [P] [US1] Unit tests for username normalization (trim, NFKC, case-fold, allowed chars, max length) in `backend/tests/unit/test_username.py`
- [ ] T020 [P] [US1] Component tests for SignUp and Login pages in `frontend/tests/`  _(substituted by Playwright E2E in `e2e/tests/auth.spec.ts`)_
- [x] T021 [P] [US1] Playwright E2E: register→login→logout in `e2e/tests/auth.spec.ts`

### Implementation for User Story 1

- [x] T022 [US1] Create `User` model (username + username_normalized, password_hash, role, status, force_password_change) in `backend/src/models/user.py`
- [ ] T023 [US1] Create Alembic migration for the `User` and `Session` tables (unique constraint on `username_normalized`) in `backend/migrations/`  _(substituted: `create_all` for v1)_
- [x] T024 [P] [US1] Pydantic schemas for register/login/user responses in `backend/src/schemas/auth.py`
- [x] T024a [P] [US1] Username normalization helper (trim/NFKC/case-fold/validate) in `backend/src/core/username.py`
- [x] T024b [P] [US1] Password-policy validator (min length + letter + number, configurable) enforced at register/admin-create/change, with unit tests, in `backend/src/core/password_policy.py`
- [x] T025 [US1] Auth service: register (Borrower only), authenticate, session create/rotate/revoke, and progressive throttling in `backend/src/services/auth.py`
- [x] T026 [US1] Auth router: `register`, `login`, `logout`, `me` with **indistinguishable** login responses for invalid/unknown/locked accounts in `backend/src/api/auth.py`
- [x] T027 [P] [US1] SignUp page (MUI form, validation) in `frontend/src/pages/SignUp.tsx`
- [x] T028 [P] [US1] Login page (MUI form, single generic error) in `frontend/src/pages/Login.tsx`
- [x] T029 [US1] Wire logout + authenticated home view and role-aware nav in `frontend/src/components/`

**Checkpoint**: User Story 1 fully functional and testable independently (MVP)

---

## Phase 4: User Story 2 — Administrator manages accounts and roles (Priority: P2)

**Goal**: An Administrator creates staff accounts, views the user list, and changes roles.

**Independent Test**: As Admin, create a Librarian, see it in the list, change a Borrower to Librarian; verify audit entries.

### Tests for User Story 2 ⚠️ (write first, must fail)

- [x] T030 [P] [US2] Contract tests for `POST /admin/users`, `GET /admin/users`, `PATCH /admin/users/{id}/role`, `PATCH /admin/users/{id}/status` in `backend/tests/integration/test_users_contract.py`
- [x] T031 [P] [US2] Integration test: admin creates staff, changes role, last-admin protection, and that deactivation revokes the user's sessions in `backend/tests/integration/test_user_management.py`
- [x] T032 [P] [US2] Authorization tests: Librarian/Borrower denied user management in `backend/tests/integration/test_authz.py`
- [ ] T033 [P] [US2] Component tests for Users management page in `frontend/tests/`  _(substituted by Playwright E2E in `e2e/tests/user-management.spec.ts`)_
- [x] T034 [P] [US2] Playwright E2E: admin creates a Librarian and changes a role in `e2e/tests/user-management.spec.ts`

### Implementation for User Story 2

- [x] T035 [P] [US2] Pydantic schemas for user create/list/role/status in `backend/src/schemas/users.py`
- [x] T036 [US2] User management service: create-with-role, list, change-role, deactivate (revoking the user's sessions), last-admin guard, audit logging in `backend/src/services/users.py`
- [x] T037 [US2] Admin users router (Administrator-only guards) in `backend/src/api/admin_users.py`
- [x] T038 [P] [US2] Users page: list, create-user dialog, role/status controls in `frontend/src/pages/Users.tsx`
- [x] T039 [US2] Add role-aware navigation entry for user management (Admin only) in `frontend/src/components/`

**Checkpoint**: User Stories 1 and 2 both work independently

---

## Phase 5: User Story 3 — Password reset via Administrator-issued temporary password (Priority: P3)

**Goal**: A user requests a reset; an Admin issues a one-time temp password; the user is forced to set a new one.

**Independent Test**: Request reset → Admin issues temp password → user logs in with it and sets a new password; old/temp passwords rejected afterward.

### Tests for User Story 3 ⚠️ (write first, must fail)

- [x] T040 [P] [US3] Contract tests for `POST /auth/reset-requests`, `GET /admin/reset-requests`, `POST /admin/reset-requests/{id}/issue`, `POST /auth/login-temporary`, `POST /auth/change-password` in `backend/tests/integration/test_reset_flow.py`
- [x] T041 [P] [US3] Integration test: full reset flow — temp-password login **atomically consumes** the grant, issues a restricted session, forced change accepts only the new password, revokes other sessions, invalidates old password; covers single-use + expiry in `backend/tests/integration/test_reset_flow.py`
- [x] T042 [P] [US3] Tests that reset submission returns an identical response for existing/unknown/deactivated users, creates a queue item only for a resolved active user, rate-limits, and consolidates duplicates in `backend/tests/integration/test_reset_flow.py`
- [ ] T043 [P] [US3] Component tests for reset request, Admin reset queue, and forced-change pages in `frontend/tests/`  _(substituted by Playwright E2E in `e2e/tests/password-reset.spec.ts`)_
- [x] T044 [P] [US3] Playwright E2E: full reset journey (request → issue → temp login → forced change) in `e2e/tests/password-reset.spec.ts`

### Implementation for User Story 3

- [x] T045 [P] [US3] Create `PasswordResetRequest` (user_id always set, status incl. cancelled, expires_at) and `TemporaryPasswordGrant` (consumed_at) models in `backend/src/models/reset.py`
- [ ] T046 [US3] Alembic migration for reset tables in `backend/migrations/`  _(substituted: `create_all` for v1)_
- [x] T047 [P] [US3] Pydantic schemas for reset request/issue, temp-password login, and forced/normal change-password in `backend/src/schemas/reset.py`
- [x] T048 [US3] Reset service: queue request (resolve active user internally, no enumeration, rate-limit, consolidate duplicates), issue one-time expiring temp password, atomic consume at temp login, forced change, invalidate old password, revoke sessions, audit logging in `backend/src/services/reset.py`
- [x] T049 [US3] Routers: public `reset-requests` + `login-temporary` + `change-password` in `backend/src/api/auth.py`; admin reset-queue/issue in `backend/src/api/admin_reset.py`
- [x] T050 [US3] Enforce the restricted `password_change` session gate (can only reach change-password) and forced-change flow in `backend/src/services/auth.py` and guards
- [x] T051 [P] [US3] Forgot-password request page in `frontend/src/pages/ForgotPassword.tsx`
- [x] T052 [P] [US3] Admin reset queue page (issue + show-once temp password; displays only resolved user, never raw input) in `frontend/src/pages/ResetQueue.tsx`
- [x] T053 [P] [US3] Forced change-password page (restricted-session flow) in `frontend/src/pages/ForceChangePassword.tsx`

**Checkpoint**: All three user stories independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T054 [P] Verify audit entries exist for all mutating actions (creation, role change, deactivation, reset request/issue) — add tests in `backend/tests/integration/test_audit.py`  _(audit entries implemented; dedicated test pending)_
- [x] T055 [P] Accessibility pass: automated **axe** checks + explicit Playwright keyboard journeys (`e2e/tests/a11y.spec.ts`) and a manual WCAG 2.1 AA review checklist (focus order/visibility, dialogs, errors, labels, contrast)
- [x] T056 Confirm ≥80% coverage for backend and frontend; fill gaps  _(backend 91%)_
- [x] T057 [P] Verify single-process deployment: `npm run build` → FastAPI serves UI + API at one origin (HTTPS/LAN config documented; dev over http)
- [ ] T057a [P] Add a tested SQLCipher→PostgreSQL migration check (open the encrypted SQLite source with the key, run migrations against Postgres, verify normalized-username uniqueness and data round-trips) in `backend/tests/integration/test_pg_migration.py`  _(deferred to cloud phase)_
- [x] T058 Run quickstart.md validation end-to-end (dev HTTP mode; packaged single-process), including the idempotent setup command re-run safety
- [x] T059 [P] Security hardening review: cookie flags (HttpOnly/Secure/SameSite), CSRF token + origin checks, throttling thresholds, session expiry/rotation/revocation, temp-password expiry, DB encryption key handling (never logged/committed), no plaintext secrets in logs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3–5)**: All depend on Foundational
  - US1 (P1) is the MVP; US2 and US3 build on the shared foundation
  - Recommended order: US1 → US2 → US3 (priority order)
- **Polish (Phase 6)**: Depends on the targeted user stories being complete

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational — delivers the MVP auth loop
- **US2 (P2)**: After Foundational; uses the `User` model from US1 but is independently testable
- **US3 (P3)**: After Foundational; depends on accounts (US1) and Administrator role (US2)

### Within Each User Story

- Tests written and failing BEFORE implementation (Test-First, NON-NEGOTIABLE)
- Models → migrations → schemas → services → routers → frontend
- Story complete before moving to the next priority

### Parallel Opportunities

- All `[P]` Setup tasks can run together
- Foundational `[P]` tasks (security helpers, audit, frontend shell) can run together
- Within a story, all `[P]` test tasks can run together, as can independent `[P]` model/schema/page tasks

---

## Implementation Strategy

**MVP first**: Complete Phase 1 → Phase 2 → Phase 3 (US1) to reach a demonstrable
authentication loop. Then layer US2 (user/role management) and US3 (password reset),
running the Polish phase last.
