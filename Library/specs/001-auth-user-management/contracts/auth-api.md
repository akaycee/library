# API Contract: Authentication, Roles & User Management

**Feature**: Authentication, Roles & User Management
**Base path**: `/api/v1`
**Format**: JSON. All requests/responses validated against schemas.

**Auth & session**: Authentication uses a server-side session. The cookie is
`HttpOnly`, `SameSite=Strict`, and `Secure`. Because `Secure` cookies require
HTTPS, the application is served over HTTPS (including on the LAN); a
development-only mode may disable `Secure` strictly for `http://127.0.0.1`. The
cookie carries only an opaque random token; the server stores its hash. Sessions
have absolute expiry and idle timeout and are rotated on login and password
change.

**CSRF**: All state-changing requests (POST/PATCH/DELETE) require a CSRF token
(double-submit: a non-HttpOnly `csrf` cookie echoed in an `X-CSRF-Token` header)
**and** pass trusted-origin validation (Origin/Referer or Fetch-Metadata). SameSite
is defense-in-depth, not the sole control.

**Non-disclosure**: Login and password-reset responses are indistinguishable for
unknown, invalid, and locked accounts, and never reveal whether a username exists.

> This is a human-readable contract. The implementation exposes the equivalent
> machine-readable OpenAPI automatically via FastAPI at `/api/v1/openapi.json`.

## Authentication

### POST /api/v1/auth/register
Self-register a Borrower. (Registration inherently reveals username availability;
this is intentional and out of scope for login/reset non-disclosure.)
- **Body**: `{ "username": string, "password": string }`
- **201**: `{ "id", "username", "role": "borrower" }`
- **409**: username unavailable
- **422**: validation error (empty/invalid/too-long username, disallowed characters, weak password)
- Maps to: FR-001, FR-002, FR-004

### POST /api/v1/auth/login
Authenticate with a normal password.
- **Body**: `{ "username": string, "password": string }`
- **200 (full session)**: `{ "id", "username", "role", "force_password_change": false }` + rotated session cookie
- **401**: single indistinguishable response for invalid credentials, unknown username, **or** a throttled/locked account (no field, existence, or lock disclosure). A `Retry-After` header MAY be sent without indicating whether the account exists.
- Maps to: FR-003, FR-006, FR-007

### POST /api/v1/auth/login-temporary
Authenticate with an Administrator-issued temporary password. On success the grant
is **atomically consumed** and a **restricted `password_change` session** is issued
that can access only `change-password`.
- **Body**: `{ "username": string, "temporary_password": string }`
- **200 (restricted session)**: `{ "force_password_change": true }` + restricted session cookie
- **401**: indistinguishable failure for invalid, already-consumed, or expired temp password
- Maps to: FR-022, FR-023

### POST /api/v1/auth/logout
- **200**: session revoked
- Maps to: FR-005

### GET /api/v1/auth/me
- **200**: current user `{ "id", "username", "role", "force_password_change" }`
- **401**: not authenticated / session expired, revoked, or user deactivated

### POST /api/v1/auth/change-password
Set a new password. Two authenticated modes:
1. **Normal change** — a full session; requires `current_password`.
2. **Forced change** — a restricted `password_change` session (from `login-temporary`);
   accepts **only** `new_password` and does not re-check the temp password.
- **Body (normal)**: `{ "current_password": string, "new_password": string }`
- **Body (forced)**: `{ "new_password": string }`
- **200**: success; clears `force_password_change`; invalidates the previous password; issues a rotated full session; revokes all other sessions
- **401**: not authenticated, wrong `current_password`, or restricted session invalid/expired
- **403**: restricted session attempting anything other than change-password
- **422**: new password fails policy
- Maps to: FR-023, FR-024, FR-007b

## Password Reset (email-free)

### POST /api/v1/auth/reset-requests
Request a reset (unauthenticated). Returns the same response in all cases and
never stores attacker-supplied text. An actionable queue item is created only for
an internally resolved **active** user; duplicate pending requests are consolidated.
Submissions are rate-limited per client/IP.
- **Body**: `{ "username": string }`
- **202**: `{ "status": "received" }` (identical for existing, unknown, and deactivated users)
- **429**: rate limit exceeded (per client/IP, not per username)
- Maps to: FR-019, FR-020, FR-025

### GET /api/v1/admin/reset-requests
List pending reset requests. **Administrator only.** Only server-resolved user
details are shown — never raw submitted text.
- **200**: `[ { "id", "username", "status", "requested_at", "expires_at" } ]`
- **403**: non-administrator
- Maps to: FR-020

### POST /api/v1/admin/reset-requests/{id}/issue
Issue a one-time temporary password. **Administrator only.**
- **200**: `{ "temporary_password": string, "expires_at": datetime }` — shown once
- **403**: non-administrator
- **404**: request not found, expired, cancelled, or already completed
- Maps to: FR-021, FR-022, FR-026

## User Management (Administrator only)

### POST /api/v1/admin/users
Create a user with any role.
- **Body**: `{ "username": string, "password": string, "role": "administrator"|"librarian"|"borrower" }`
- **201**: created user
- **403**: non-administrator
- **409**: username unavailable
- Maps to: FR-012, FR-015

### GET /api/v1/admin/users
List users with roles and status.
- **200**: `[ { "id", "username", "role", "status" } ]`
- **403**: non-administrator
- Maps to: FR-016

### PATCH /api/v1/admin/users/{id}/role
Change a user's role.
- **Body**: `{ "role": "administrator"|"librarian"|"borrower" }`
- **200**: updated user; audit entry written
- **403**: non-administrator
- **409**: would remove the last active Administrator
- Maps to: FR-017, FR-014, FR-026

### PATCH /api/v1/admin/users/{id}/status
Deactivate (soft-delete) or reactivate a user.
- **Body**: `{ "status": "active"|"deactivated" }`
- **200**: updated user
- **403**: non-administrator
- **409**: would deactivate the last active Administrator
- Maps to: FR-018, FR-014

## Authorization Matrix

| Endpoint group            | Unauth | Restricted (pwd-change) | Borrower | Librarian | Administrator |
|---------------------------|:------:|:-----------------------:|:--------:|:---------:|:-------------:|
| auth/register, auth/login, auth/login-temporary, auth/reset-requests | ✅ | — | — | — | — |
| auth/change-password (forced) | ❌ | ✅ | — | — | — |
| auth/me, auth/logout, auth/change-password (normal) | ❌ | ❌ | ✅ | ✅ | ✅ |
| admin/reset-requests/*    | ❌ | ❌ | ❌ | ❌ | ✅ |
| admin/users/*             | ❌ | ❌ | ❌ | ❌ | ✅ |

Maps to: FR-008, FR-009, FR-010, FR-011

## Cross-cutting

- Every mutating admin action writes an append-only `AuditLogEntry` (FR-026, FR-027).
- All state-changing requests require a valid CSRF token and pass trusted-origin validation (FR-007c).
- All endpoints return validation errors at the boundary via schema validation.
- Every authorization check rejects sessions that are expired, revoked, idle-timed-out, or belong to a deactivated user (FR-007b).
