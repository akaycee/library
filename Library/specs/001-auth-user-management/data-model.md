# Phase 1 Data Model: Authentication, Roles & User Management

**Feature**: Authentication, Roles & User Management
**Date**: 2026-07-19

This model is implemented with SQLAlchemy 2.x. The local database is stored
**encrypted at rest** using SQLCipher; the encryption key is supplied at startup
(configuration/environment) and is never committed or logged. It is designed to
migrate to PostgreSQL, but this is a **tested migration project**, not a
connection-string swap: enum representation, case/collation handling, timestamp
timezone, and UUID types differ between SQLite/SQLCipher and PostgreSQL and are
exercised by migration tests (see quickstart.md).

## Entities

### User

Represents a person who can authenticate.

| Field                    | Type        | Notes |
|--------------------------|-------------|-------|
| id                       | UUID/int PK | Primary key |
| username                 | string      | The username as originally entered (display form), NOT an email |
| username_normalized      | string      | Unique. Trimmed, Unicode NFKC-normalized, case-folded form used for uniqueness and lookup |
| password_hash            | string      | Argon2id hash only; never plaintext |
| role                     | enum        | One of `administrator`, `librarian`, `borrower` |
| status                   | enum        | `active` or `deactivated` (soft-delete) |
| force_password_change    | boolean     | True after a temp-password login until the user sets a new password |
| created_at               | datetime    | Stored in UTC |
| updated_at               | datetime    | Stored in UTC |

**Username rules**:
- Input is trimmed of leading/trailing whitespace and rejected if empty.
- Normalized via Unicode NFKC + case-folding into `username_normalized`.
- Allowed characters: letters, digits, and `. _ -`; maximum length 32 (configurable).
- Uniqueness is enforced by a UNIQUE constraint on `username_normalized`, so it is
  portable across SQLite and PostgreSQL without relying on database collation.

**Rules**:
- Self-registration always sets `role = borrower` (FR-001, FR-012).
- Administrator/Librarian roles set only by an Administrator (FR-012, FR-015).
- At least one `administrator` with `status = active` MUST always exist (FR-014).
- Deactivation sets `status = deactivated`; the row is retained (FR-018).
- A `deactivated` user MUST be rejected on every authorization check and all their
  sessions MUST be revoked at deactivation.

### Session

Server-side session backing the auth cookie. The cookie carries only an opaque
random token; the server stores its hash.

| Field         | Type        | Notes |
|---------------|-------------|-------|
| id            | UUID PK     | |
| user_id       | FK → User   | Owner of the session |
| token_hash    | string      | Hash (SHA-256) of the opaque session token; the raw token is never stored |
| kind          | enum        | `full` (normal session) or `password_change` (restricted, see below) |
| created_at    | datetime    | UTC |
| expires_at    | datetime    | Absolute expiry; idle timeout enforced via `last_seen_at` |
| last_seen_at  | datetime    | Updated on activity for idle-timeout checks |
| revoked_at    | datetime    | Non-null once revoked; revoked sessions are always rejected |

**Rules**:
- A new session is created at login and the token is **rotated** (old session
  revoked, new one issued) on privilege-relevant transitions: successful login and
  password change (prevents fixation).
- Logout sets `revoked_at`.
- Every authorization check MUST reject sessions that are expired, revoked, idle
  past timeout, or whose user is `deactivated`.
- Password reset completion revokes **all** of the user's existing sessions.
- `kind = password_change` sessions are short-lived and may ONLY access the
  change-password endpoint (see Temporary-password flow).

### PasswordResetRequest

An email-free reset request that drives the Administrator queue. A queue item is
created only for an internally resolved **active** user; the public response is
identical regardless.

| Field            | Type        | Notes |
|------------------|-------------|-------|
| id               | UUID/int PK | |
| user_id          | FK → User   | Always set — created only after internally resolving an active user |
| status           | enum        | `pending`, `issued`, `completed`, `expired`, `cancelled` |
| requested_at     | datetime    | UTC |
| expires_at       | datetime    | Pending requests expire if not actioned (configurable) |
| issued_at        | datetime    | Set when an Administrator issues a temp password |
| completed_at     | datetime    | Set when the user sets a new password |

**Rules**:
- The submission endpoint returns the same public response whether or not the
  username resolves (FR-025); attacker-supplied text is never stored or displayed.
- At most one `pending` request per user: duplicate submissions consolidate into
  the existing pending request rather than creating new rows.
- Submissions are rate-limited per client/IP to prevent queue spam.
- Only Administrators can transition `pending → issued` (FR-021).

### TemporaryPasswordGrant

The one-time credential issued for a reset.

| Field         | Type        | Notes |
|---------------|-------------|-------|
| id            | UUID/int PK | |
| user_id       | FK → User   | |
| request_id    | FK → PasswordResetRequest | |
| temp_hash     | string      | Argon2id hash of the temporary password |
| expires_at    | datetime    | Configurable window (default 24h) |
| consumed_at   | datetime    | Set atomically at temp-password **login**; null until then |

**Rules & state machine**:
- A grant is in one of: `active` (not consumed, not expired), `consumed`, or `expired`.
- On a temp-password **login**, the grant is **atomically consumed**
  (`consumed_at` set) in the same transaction, and a restricted
  `password_change` session is issued. The temp password is never accepted again.
- The forced-change endpoint is authenticated **only** by that restricted session
  and accepts **only the new password** — it does not re-check the temp password
  (resolves the consume-vs-verify inconsistency).
- Setting the new password creates a full session (rotated), marks the request
  `completed`, revokes all other sessions, and invalidates the previous password.
- A grant past `expires_at` with null `consumed_at` is `expired` and may be reissued.
- Displayed in plaintext exactly once to the issuing Administrator; never stored in plaintext.

### AuditLogEntry

Append-only record of account/security actions.

| Field       | Type        | Notes |
|-------------|-------------|-------|
| id          | UUID/int PK | |
| actor_id    | FK → User   | Who performed the action (nullable for system/bootstrap) |
| action      | enum/string | e.g., `user.create`, `role.change`, `user.deactivate`, `reset.request`, `reset.issue`, `password.change` |
| target_id   | FK → User   | The affected user, when applicable || reason      | string      | The "why" for the action (e.g., "role changed to librarian by admin"); required by constitution Principle II || detail      | string/json | Before/after where relevant (e.g., old→new role) |
| created_at  | datetime    | |

**Rules**:
- Insert-only; no update/delete through application flows (FR-027).
- One entry per account creation, role change, deactivation, reset request, and
  temp-password issuance (FR-026).

## Relationships

- `User (1) → (many) Session`
- `User (1) → (many) PasswordResetRequest`
- `PasswordResetRequest (1) → (0..many) TemporaryPasswordGrant` (reissue on expiry)
- `User (1) → (many) AuditLogEntry` as actor and as target

## Enumerations

- **Role**: `administrator` | `librarian` | `borrower`
- **UserStatus**: `active` | `deactivated`
- **SessionKind**: `full` | `password_change`
- **ResetStatus**: `pending` | `issued` | `completed` | `expired` | `cancelled`

## Seeding

- Provisioning the bootstrap Administrator is handled by an **idempotent setup
  command** (see quickstart.md and spec FR-013), not a blind seed:
  - It creates the Administrator transactionally **only when no users exist**.
  - It either prompts for a password interactively or generates a random one
    shown exactly once; it refuses well-known/default credentials.
  - The password is never written to logs.
  - Re-runs are safe: if any user already exists, it makes no changes.
  - The account is created with `force_password_change = true`.
