# Feature Specification: Librarian Dashboard

**Feature Branch**: `006-librarian-dashboard`

**Created**: 2026-07-21

**Status**: Implemented

**Input**: User description: "A staff dashboard that surfaces at-a-glance library
health — collection size, circulation state, overdue items, active borrowers, and
the password-reset queue — with a quick way to act on overdue loans."

## Clarifications (resolved with the user)

- **Audience**: Staff only (Librarians and Administrators). Borrowers cannot see it.
- **Placement**: A separate `/dashboard` route; the role-aware Home page is unchanged.
- **Stats**: Total titles & copies, copies on loan, copies available, overdue count,
  active borrowers (with an open loan), and pending password-reset requests.
- **Overdue panel**: A table (borrower, item, due date, days overdue) with a quick
  Return action inline.
- **Recent activity**: The last 10 circulation events (checkouts / returns / renewals).
- **Read model**: All figures are derived on demand from existing data; no new
  denormalized counters.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See library health at a glance (Priority: P1) 🎯 MVP

A librarian opens the dashboard and sees current stats: how many titles and copies
exist, how many are on loan vs available, how many loans are overdue, how many
borrowers currently hold an item, and how many password resets are waiting.

**Why this priority**: The core value of the dashboard is the at-a-glance snapshot;
it stands alone and is useful immediately.

**Independent Test**: With seeded copies and loans, open `/dashboard`; each stat
card shows the correct number matching the underlying data.

**Acceptance Scenarios**:

1. **Given** signed-in staff, **When** they open the dashboard, **Then** stat cards show titles, copies, on-loan, available, overdue, active borrowers, and pending resets.
2. **Given** a copy is checked out, **When** the dashboard is (re)loaded, **Then** on-loan increases by one and available decreases by one.
3. **Given** a borrower cannot self-serve, **When** a borrower navigates to `/dashboard`, **Then** they are redirected away (staff-only).

### User Story 2 - Act on overdue loans (Priority: P1) 🎯 MVP

The dashboard lists overdue loans (borrower, item, due date, days overdue). The
librarian can process a return directly from the panel.

**Why this priority**: Overdue follow-up is the primary action a librarian takes
from a dashboard; pairs with Story 1 for the MVP.

**Independent Test**: With an overdue loan present, the panel lists it with the
correct days-overdue; clicking Return clears it and updates the stats.

**Acceptance Scenarios**:

1. **Given** an overdue loan, **When** the dashboard loads, **Then** it appears in the overdue panel with borrower, item, due date, and days overdue.
2. **Given** an overdue loan in the panel, **When** staff click Return, **Then** the loan is returned, the row disappears, and overdue/available stats update.
3. **Given** no overdue loans, **When** the dashboard loads, **Then** the panel shows an empty state.

### User Story 3 - Review recent circulation activity (Priority: P2)

The dashboard shows the last 10 circulation events so staff can see what just
happened at the desk.

**Why this priority**: Situational awareness; valuable but not required for the
core snapshot + overdue action.

**Independent Test**: After a checkout and a return, the activity feed lists both,
most-recent first.

**Acceptance Scenarios**:

1. **Given** recent checkouts/returns/renewals, **When** the dashboard loads, **Then** up to 10 events are listed newest-first with the action and when.

## Requirements *(mandatory)*

- **FR-001**: The system MUST expose a staff-only dashboard summary combining
  collection counts, circulation state, overdue count, active-borrower count, and
  pending password-reset count.
- **FR-002**: The system MUST list overdue loans with borrower, item, due date, and
  days overdue, and allow returning a loan from the dashboard.
- **FR-003**: The system MUST list the most recent 10 circulation events (checkout,
  return, renew) newest-first.
- **FR-004**: All dashboard data MUST be restricted to Librarians and Administrators.
- **FR-005**: Figures MUST be derived from live data (copies, loans, reset requests,
  audit log); no new persistent counters are introduced.

## Success Criteria

- **SC-001**: Every stat card matches a direct query of the underlying data.
- **SC-002**: Returning an overdue loan from the dashboard updates the panel and the
  overdue/available/on-loan stats without a manual refresh.
- **SC-003**: Borrowers cannot reach the dashboard route or its API.
- **SC-004**: The dashboard page has no serious accessibility violations (WCAG 2.1 AA).
