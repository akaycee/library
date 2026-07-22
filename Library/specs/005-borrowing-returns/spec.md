# Feature Specification: Borrowing & Returns

**Feature Branch**: `005-borrowing-returns`

**Created**: 2026-07-20

**Status**: Implemented

**Input**: User description: "Borrowing and returns — staff check out copies to borrowers at a desk, with per-checkout loan periods, renewals, and overdue tracking. No item limit."

## Clarifications (resolved with the user)

- **Who checks out**: Staff-only desk model — Librarians and Administrators check
  out and return on a borrower's behalf. Borrowers do not self-checkout.
- **Loan period**: Entered per checkout (staff sets the number of days); no fixed
  library-wide period. No limit on how many items a borrower may hold.
- **Renewals**: Allowed — extends the due date, unless the loan is already overdue.
- **Overdue**: Tracked and flagged (for the librarian dashboard); no fines in v1.
- **No email**: Overdue is surfaced in-app only.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Check out a copy (Priority: P1) 🎯 MVP

At the desk, a librarian checks out a specific copy (by barcode) to a borrower (by
username), entering a loan period in days. The copy becomes checked out and a loan
is recorded with a due date.

**Why this priority**: Circulation is the core purpose of a lending library; this
is the foundational transaction and stands alone.

**Independent Test**: Check out an available copy to a borrower for 14 days; the
copy shows `checked_out`, a loan exists with the correct due date, and availability
drops accordingly.

**Acceptance Scenarios**:

1. **Given** a signed-in staff member, an available copy, and an active borrower, **When** they check the copy out for N days, **Then** a loan is created, the copy becomes `checked_out`, and the due date is N days out.
2. **Given** a copy that is already `checked_out` (or lost/withdrawn), **When** staff try to check it out, **Then** it is refused.
3. **Given** an unknown barcode or unknown/inactive borrower, **When** staff try to check out, **Then** it is refused with a clear message.
4. **Given** a checkout, **When** availability is viewed (browse), **Then** the available count reflects the checkout.

### User Story 2 - Return a copy (Priority: P1) 🎯 MVP

A librarian processes a return; the copy becomes available again.

**Why this priority**: The other half of the core loop; required for the MVP.

**Independent Test**: Return an active loan; the copy becomes `available` and the
loan is marked returned.

**Acceptance Scenarios**:

1. **Given** an active loan, **When** staff return it, **Then** the loan is marked returned (with a timestamp) and the copy becomes `available`.
2. **Given** a copy that is not on loan, **When** staff try to return it, **Then** it is refused.

### User Story 3 - Renew and track overdue (Priority: P2)

Staff renew an active, non-overdue loan (extending the due date). Overdue loans are
flagged.

**Independent Test**: Renew a loan by M days → due date extends; a loan past its due
date shows as overdue; renewing an overdue loan is refused.

**Acceptance Scenarios**:

1. **Given** an active, non-overdue loan, **When** staff renew it by M days, **Then** the due date is extended and the renewal count increases.
2. **Given** an overdue loan, **When** staff try to renew it, **Then** it is refused.
3. **Given** loans past their due date, **When** staff view active loans, **Then** those loans are marked overdue.

### User Story 4 - Borrower views their loans (Priority: P3)

A borrower sees the items currently checked out to them and their due dates.

**Independent Test**: As a borrower with an active loan, view "My loans" and see the
title and due date.

**Acceptance Scenarios**:

1. **Given** a signed-in borrower with active loans, **When** they open "My loans", **Then** they see each loan's title and due date (read-only).
2. **Given** a borrower with no loans, **When** they open "My loans", **Then** they see an empty state.

### Edge Cases

- What happens if two staff check out the same copy at once? → Only the first succeeds; the copy is then `checked_out`.
- What loan period values are valid? → A positive number of days; zero/negative is refused.
- Can a lost/withdrawn copy be checked out? → No; only `available` copies.
- Deleting a checked-out copy or manually changing its status? → Already refused by the catalog feature while on loan.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Only staff (Administrator or Librarian) may check out, return, or renew loans; Borrowers may not perform circulation actions.
- **FR-002**: Staff MUST be able to check out an `available` copy (identified by barcode) to an active borrower (identified by username) with a per-checkout loan period in days (> 0).
- **FR-003**: A checkout MUST set the copy to `checked_out`, create a loan with a due date (now + days), and record who checked it out.
- **FR-004**: The system MUST refuse checkout of a copy that is not `available`, or to an unknown/inactive borrower, or with a non-positive loan period.
- **FR-005**: Staff MUST be able to return an active loan; returning MUST mark the loan returned and set the copy back to `available`.
- **FR-006**: Staff MUST be able to renew an active loan that is not overdue, extending its due date and increasing its renewal count; renewing an overdue loan MUST be refused.
- **FR-007**: The system MUST identify overdue loans (active, past due date) and expose them to staff.
- **FR-008**: There is no limit on the number of concurrent loans per borrower.
- **FR-009**: A borrower MUST be able to view their own active loans (title + due date), read-only.
- **FR-010**: Every checkout, return, and renewal MUST be recorded in the audit log with who/what/when/why.
- **FR-011**: Availability (browse) MUST reflect loans in real time (a checked-out copy is not available).

### Key Entities *(include if feature involves data)*

- **Loan**: A borrowing record. Attributes: id, copy (ref), borrower (user ref), checked-out-by (staff user ref), borrowed_at, due_at, returned_at (null while active), renewal_count. Relationships: a Loan is for one Copy and one borrower.

## Success Criteria *(mandatory)*

- **SC-001**: A librarian can check out a copy to a borrower in under 30 seconds (barcode + username + days).
- **SC-002**: A checked-out copy is never simultaneously loaned to two borrowers.
- **SC-003**: Availability shown in browse matches actual loans 100% of the time.
- **SC-004**: Overdue loans are correctly flagged 100% of the time (active + past due).
- **SC-005**: 100% of checkout/return/renew actions produce an audit log entry.

## Assumptions

- Reuses the catalog (Title/Copy), users/roles, staff guards, and audit infrastructure.
- Checkout identifies the copy by barcode and the borrower by username (desk-friendly).
- Loan period is provided per checkout; a sensible default (e.g., 14) may be pre-filled in the UI but is not enforced server-side beyond > 0.
- Renewal extends the due date from the current due date by the given days.
- Overdue is derived (due_at < now and not returned); no notifications/fines in v1.
- The librarian dashboard (aggregate overdue view) is a separate later feature (F9);
  this feature exposes the data it needs.
