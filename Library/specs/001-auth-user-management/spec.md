# Feature Specification: Authentication, Roles & User Management

**Feature Branch**: `001-auth-user-management`

**Created**: 2026-07-19

**Status**: Implemented (US1, US2, US3) — 36 backend tests + 10 Playwright E2E passing; backend coverage 91%

**Input**: User description: "Set up the UI with sign up and login pages and the necessary backend. Add roles: Administrator (access to everything), Librarian (all library inventory tasks), Borrower (borrow and return only). No email in v1 — usernames are not emails and password resets are handled by an Administrator issuing a one-time temporary password."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Borrower self-registration and login (Priority: P1)

A new borrower creates their own account, then signs in to access the system. This is the entry point for the largest group of users and the foundation every other feature depends on.

**Why this priority**: Without account creation and login, no one can use the system. Borrower self-registration is the highest-volume path and delivers immediate standalone value (people can register and authenticate).

**Independent Test**: Register a new borrower with a username and password, log out, and log back in with those credentials. Delivers a working authentication loop end-to-end.

**Acceptance Scenarios**:

1. **Given** a visitor on the sign-up page, **When** they submit a unique username and a valid password, **Then** a Borrower account is created and they are signed in (or directed to the login page).
2. **Given** a registered borrower on the login page, **When** they submit correct credentials, **Then** they are authenticated and see the borrower home view.
3. **Given** a registered borrower, **When** they submit an incorrect password, **Then** authentication is refused with a single generic response that does not reveal which field was wrong, whether the username exists, or whether the account is locked.
4. **Given** a signed-in user, **When** they choose to log out, **Then** their session is ended and protected views are no longer accessible.
5. **Given** a visitor entering a username that already exists, **When** they submit sign-up, **Then** registration is refused with a clear "username unavailable" message.

---

### User Story 2 - Administrator manages accounts and roles (Priority: P2)

An Administrator creates staff accounts (Librarian or Administrator), views the user list, and changes a user's role. Administrator and Librarian accounts cannot be self-registered — they are provisioned by an Administrator.

**Why this priority**: Staff accounts and role assignment are required before inventory/circulation features can be operated, but they build on top of the working auth loop from US1.

**Independent Test**: As an Administrator, create a Librarian account, verify it appears in the user list with the Librarian role, then change a Borrower's role to Librarian and confirm the change is recorded.

**Acceptance Scenarios**:

1. **Given** a signed-in Administrator, **When** they create an account and assign it the Librarian role, **Then** the account exists with that role and can sign in.
2. **Given** a signed-in Administrator viewing the user list, **When** they change a user's role, **Then** the new role takes effect and the change is written to the audit log with who/what/when.
3. **Given** a signed-in Librarian or Borrower, **When** they attempt to access user management, **Then** access is denied.
4. **Given** the very first system startup with no users, **When** the system is initialized, **Then** a single bootstrap Administrator account exists so the system can be administered.
5. **Given** an Administrator, **When** they attempt to remove or demote the last remaining Administrator, **Then** the action is refused to prevent lockout.

---

### User Story 3 - Password reset via Administrator-issued temporary password (Priority: P3)

A user who forgot their password requests a reset. The request appears in the Administrator's queue. After verifying the person, the Administrator issues a one-time temporary password shown once on screen. The user signs in with it and is immediately forced to set a new password.

**Why this priority**: Important for real-world operation but not required to prove the core auth loop; it depends on both US1 (accounts) and US2 (Administrator role).

**Independent Test**: As a user, submit a reset request; as an Administrator, action the request and capture the temporary password; as the user, sign in with the temporary password and set a new one; confirm the old and temporary passwords no longer work.

**Acceptance Scenarios**:

1. **Given** a user on the login page, **When** they request a password reset for their username, **Then** a reset request is queued for Administrators (no email is sent).
2. **Given** an Administrator with a pending reset request, **When** they issue a reset, **Then** a one-time temporary password is generated and displayed once to the Administrator only.
3. **Given** a user with an issued temporary password, **When** they sign in with it, **Then** they are required to set a new password before accessing anything else.
4. **Given** an issued temporary password, **When** it has already been used once or has expired, **Then** it is rejected.
5. **Given** a completed reset, **When** the user's previous password is tried, **Then** it is rejected.

---

### Edge Cases

- What happens when a username contains only whitespace, is empty, or exceeds the allowed length? → Registration/creation is refused with a validation message.
- How does the system handle repeated failed login attempts? → Progressive throttling keyed by **both account and client/IP**, with a bounded lock duration and automatic recovery, so one person cannot lock another out indefinitely (documented in Assumptions).
- What happens when two people request the same new username simultaneously? → Only the first succeeds; the second gets "username unavailable" (registration is authenticated-visitor-facing and inherently reveals uniqueness).
- What happens if an Administrator issues a temporary password but the user never uses it? → It expires after the configured window and can be reissued.
- What happens when a temporary password is used to log in? → It is atomically consumed at login and cannot be used again; the user gets a restricted session that can only set a new password.
- What happens when a user with an active session has their role changed? → New permissions apply on the next authorization check (documented in Assumptions).
- What happens when a user is deactivated while they have an active session? → Their sessions are revoked and every subsequent authorization check is rejected.
- What happens when a reset is requested for a non-existent or deactivated username? → The public response is identical to the success case; an actionable queue item is created only for an internally resolved active user, and attacker-supplied text is never stored or shown.

## Requirements *(mandatory)*

### Functional Requirements

**Authentication**

- **FR-001**: System MUST allow a visitor to self-register a Borrower account using a username and password.
- **FR-002**: Usernames MUST be unique, non-empty, and MUST NOT be treated as or required to be email addresses.
- **FR-003**: System MUST authenticate users by verifying username and password, and MUST store passwords only in a securely hashed form (never in plaintext or reversible form).
- **FR-004**: System MUST enforce a minimum password strength policy (documented in Assumptions) and reject non-conforming passwords at registration and reset.
- **FR-005**: System MUST allow authenticated users to log out, ending (revoking) their session.
- **FR-006**: System MUST return an indistinguishable authentication response for invalid credentials, unknown usernames, and locked accounts — disclosing neither which field was wrong nor whether the account exists or is locked.
- **FR-007**: System MUST apply progressive login throttling keyed by both account and client/IP, with a bounded lock duration and automatic recovery, and MUST resist using lockout to deny service to a legitimate user.
- **FR-007a**: System MUST maintain server-side sessions where the cookie carries only an opaque random token and the server stores only its hash; sessions MUST have absolute expiry and idle timeout.
- **FR-007b**: System MUST rotate the session (revoke old, issue new) on login and on password change, and MUST reject sessions that are expired, revoked, idle-timed-out, or whose user is deactivated.
- **FR-007c**: System MUST protect all state-changing requests against CSRF using a token (e.g., double-submit) plus trusted-origin validation, in addition to SameSite cookies.

**Roles & Authorization**

- **FR-008**: System MUST support exactly three roles: Administrator, Librarian, and Borrower.
- **FR-009**: System MUST grant Administrators access to all functions, including user and role management.
- **FR-010**: System MUST grant Librarians access to library/inventory operations but MUST deny them system administration (user/role management).
- **FR-011**: System MUST restrict Borrowers to catalog viewing, their own account, and borrowing/returning; all other write operations MUST be denied.
- **FR-012**: System MUST deny self-registration of Administrator or Librarian roles; those accounts MUST be created by an Administrator.
- **FR-013**: System MUST provide exactly one bootstrap Administrator account on first initialization so the system is administrable.
- **FR-014**: System MUST prevent removal or demotion of the last remaining Administrator.

**User Management**

- **FR-015**: Administrators MUST be able to create user accounts and assign any of the three roles.
- **FR-016**: Administrators MUST be able to view a list of users with their roles and account status.
- **FR-017**: Administrators MUST be able to change a user's role.
- **FR-018**: Administrators MUST be able to deactivate (soft-delete) a user account without erasing history.

**Password Reset (no email)**

- **FR-019**: Users MUST be able to submit a password reset request from the login flow without email.
- **FR-020**: System MUST place reset requests in a queue visible to Administrators.
- **FR-021**: Administrators MUST be able to issue a one-time temporary password that is displayed exactly once to the Administrator.
- **FR-022**: Temporary passwords MUST be single-use — atomically consumed at login — and MUST expire after a configured time window.
- **FR-023**: A temporary-password login MUST grant only a restricted session that can do nothing except set a new password; the user MUST set a new password before any other function.
- **FR-024**: Completing a reset MUST invalidate the previous password and revoke all of the user's other sessions.
- **FR-025**: The reset submission endpoint MUST return an identical public response whether or not the username resolves; it MUST NOT store or display attacker-supplied text, MUST create an actionable queue item only for an internally resolved active user, MUST rate-limit submissions, and MUST consolidate duplicate pending requests.

**Auditability (per constitution)**

- **FR-026**: System MUST log account creation, role changes, deactivations, password reset requests, and temporary-password issuance with who, what, and when.
- **FR-027**: Audit records MUST be append-only and MUST NOT be editable through normal application flows.

**Data Protection (per constitution)**

- **FR-030**: All persisted data containing user/PII (the database, including usernames and account records) MUST be encrypted at rest; the local database MUST use an encrypted-at-rest store, and its encryption key MUST be supplied at startup and never committed to source or written to logs.
- **FR-031**: Data in transit MUST be protected with HTTPS/TLS for all non-loopback access.

**Usability & Accessibility (per constitution)**

- **FR-028**: Sign-up, login, user management, and reset screens MUST be built on accessible Material Design foundations (MUI) and MUST be verified against WCAG 2.1 AA using automated axe checks, explicit keyboard-navigation journeys, and a manual review checklist (focus order, focus visibility, dialogs, error messaging, form labels, and contrast).
- **FR-029**: Navigation MUST be role-aware, showing users only the actions they are permitted to perform.

### Key Entities *(include if feature involves data)*

- **User**: A person who can authenticate. Attributes: display username plus a normalized username for uniqueness/lookup, hashed password, role, account status (active/deactivated), timestamps, flag indicating a forced password change is pending.
- **Session**: A server-side session backing the auth cookie; holds a hashed opaque token, owner, kind (full or restricted password-change), creation/expiry/last-seen timestamps, and a revocation timestamp.
- **Role**: One of Administrator, Librarian, Borrower, defining the set of permitted actions.
- **Password Reset Request**: A queue item tied to an internally resolved active user, with status (pending/issued/completed/expired/cancelled) and timestamps; drives the Administrator queue.
- **Temporary Password Grant**: A one-time, expiring credential issued for a reset, consumed atomically at login.
- **Audit Log Entry**: An append-only record of a security- or account-affecting action (actor, action, target, timestamp).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new borrower can complete registration and reach their home view in under 2 minutes on first attempt.
- **SC-002**: 95% of test users can log in successfully on the first attempt with correct credentials without assistance.
- **SC-003**: An Administrator can create a staff account and assign a role in under 1 minute.
- **SC-004**: 100% of account creations, role changes, deactivations, and reset issuances produce an audit log entry.
- **SC-005**: A full password reset (request → Administrator issuance → user sets new password) can be completed in under 3 minutes with no email involved.
- **SC-006**: No **login or password-reset** screen exposes whether a username exists to an unauthenticated user. (Open self-registration necessarily reveals whether a chosen username is available and is out of scope for this criterion.)
- **SC-007**: All feature screens pass automated axe accessibility checks and explicit Playwright keyboard-navigation journeys, and clear a manual WCAG 2.1 AA review checklist.

## Assumptions

- v1 runs entirely locally, including its database; no email or external notification service is available (consistent with the constitution).
- Password policy default: minimum 8 characters with at least one letter and one number; adjustable later. The policy is enforced consistently at registration, admin user-creation, and password change/reset.
- Username rules: trimmed, Unicode NFKC-normalized and case-folded for uniqueness; allowed characters are letters, digits, and `. _ -`; maximum length 32 (configurable).
- Login throttling default: progressive delay then a temporary lock after repeated failures within a short window, keyed by both account and client/IP; lock duration is bounded and self-recovering; thresholds are configurable.
- Sessions: opaque token in an HttpOnly cookie with the hash stored server-side; absolute expiry (default 12h) and idle timeout (default 30m), both configurable; rotated at login and password change.
- Temporary password expiry default: 24 hours or first (consuming) login, whichever comes first; configurable.
- Role changes take effect on the next authorization check; active sessions are not force-terminated on a role change in v1 (deactivation, by contrast, does revoke sessions).
- Identity verification for a password reset is performed out-of-band by the Administrator (in person or by phone), appropriate for a single local library.
- Borrower self-registration is open in v1; gating or approval of self-registration is out of scope for this feature.
- The bootstrap Administrator is provisioned by an idempotent setup command that creates the account only when no users exist, prompts for or generates a one-time password (never logged), refuses default credentials, and forces a change on first login.
- Transport security: v1 is intended to run over HTTPS (including on the LAN) so that Secure cookies are honored; a development-only non-Secure cookie mode is available strictly for local `http://127.0.0.1` use.
- Encryption at rest: the local database is stored encrypted (SQLCipher). The encryption key is provided via configuration/environment at startup, kept out of source control and logs, and required to open the database. This is an accepted, justified addition over a plain SQLite file to satisfy the constitution's PII-at-rest mandate while remaining a self-contained, zero-server local store.
