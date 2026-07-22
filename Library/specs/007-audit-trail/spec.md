# Feature Specification: Audit Trail & Logging

**Feature Branch**: `007-audit-trail`

**Created**: 2026-07-21

**Status**: Implemented

**Input**: User description: "A staff-facing audit trail that surfaces the existing
append-only log — who did what, when, and why — with filtering by action, actor or
target, and date range."

## Clarifications (resolved with the user)

- **Audience**: All staff (Librarians and Administrators) can view the audit trail.
  Borrowers cannot.
- **Filtering**: By action type, by actor/target username (search), and by date
  range.
- **Read-only**: The log is append-only (constitution II). No feature edits or
  deletes entries; this is a viewer over data already written across features.
- **Resolution**: Actor and target user ids are resolved to usernames for display;
  system/bootstrap entries (no actor) show as "system".
- **Ordering & paging**: Newest-first, paginated to keep the view lightweight.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review recent actions (Priority: P1) 🎯 MVP

A librarian opens the audit trail and sees a newest-first list of actions across
the system: the action, who performed it, who/what it targeted, the reason, and
when.

**Why this priority**: The core value — accountability and traceability — is
delivered by simply making the existing log visible; it stands alone.

**Independent Test**: After a few actions (a checkout, a title edit), open the
audit page; those entries appear newest-first with actor, action, reason, and time.

**Acceptance Scenarios**:

1. **Given** signed-in staff, **When** they open the audit trail, **Then** entries are listed newest-first with action, actor, target, reason, and timestamp.
2. **Given** an entry performed by the system (no actor), **When** it is shown, **Then** the actor reads "system".
3. **Given** a borrower, **When** they attempt to reach the audit trail or its API, **Then** they are refused.

### User Story 2 - Filter the trail (Priority: P1) 🎯 MVP

Staff narrow the trail by action type, by a username (actor or target), and by a
date range to find specific events.

**Why this priority**: A growing log is only useful if it can be filtered; pairs
with Story 1 for the MVP.

**Independent Test**: With mixed entries, filtering by action `loan.checkout`
returns only checkouts; filtering by a username returns only that user's entries;
a date range excludes entries outside it.

**Acceptance Scenarios**:

1. **Given** entries of several action types, **When** staff filter by an action, **Then** only entries of that action are returned.
2. **Given** entries for different users, **When** staff search a username, **Then** only entries where that user is the actor or target are returned.
3. **Given** entries across days, **When** staff set a from/to date, **Then** only entries within the range are returned.

## Requirements *(mandatory)*

- **FR-001**: The system MUST expose a staff-only, read-only listing of audit
  entries, newest-first, resolving actor/target ids to usernames.
- **FR-002**: The listing MUST support filtering by action type, by actor/target
  username (case-insensitive contains), and by a from/to date range.
- **FR-003**: The listing MUST be paginated (limit + offset) with a sensible cap.
- **FR-004**: The system MUST expose the set of distinct action types to populate a
  filter control.
- **FR-005**: The audit data MUST NOT be modifiable through any endpoint
  (append-only; constitution II).

## Success Criteria

- **SC-001**: Every action performed by other features appears in the trail without
  additional wiring (it reads the shared log).
- **SC-002**: Filtering by action, username, and date range each returns exactly the
  matching entries.
- **SC-003**: Borrowers cannot reach the audit route or its API.
- **SC-004**: The audit page has no serious accessibility violations (WCAG 2.1 AA).
