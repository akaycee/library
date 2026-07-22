# Feature Specification: Catalog Search & Browse

**Feature Branch**: `004-catalog-search`

**Created**: 2026-07-20

**Status**: Implemented (US1, US2) — 4 backend tests + 2 Playwright E2E passing; borrower-facing read-only browse/search

**Input**: User description: "Search and browse the catalog with real-time availability, accessible to all roles including Borrowers."

## Clarifications (resolved with reasonable defaults)

- **Audience**: Any signed-in user — Borrowers, Librarians, Administrators. This is
  the first borrower-facing feature.
- **Search fields**: Case-insensitive substring match across title name, author,
  and ISBN.
- **Availability**: Shown per title as "N of M available", where availability
  counts copies with status `available`, computed live (real-time).
- **Privacy**: The borrower-facing view exposes title info + availability only —
  not internal barcodes or exact shelf locations (those remain staff-only via the
  catalog management feature).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse the catalog (Priority: P1) 🎯 MVP

A borrower opens the catalog and sees the library's titles with their availability,
so they know what they can borrow.

**Why this priority**: This is the core borrower value and the entry point for
borrowing later; it stands alone (people can see holdings).

**Independent Test**: As a borrower, open Browse and see a list of titles each
showing an availability indicator.

**Acceptance Scenarios**:

1. **Given** a signed-in user of any role, **When** they open the browse page, **Then** they see titles with author, media type, and availability (N of M available).
2. **Given** a title with 2 of 3 copies available, **When** it is displayed, **Then** availability shows "2 of 3 available".
3. **Given** a title whose copies are all checked out/lost/withdrawn, **When** it is displayed, **Then** it shows "Not available" (0 available).

### User Story 2 - Search the catalog (Priority: P2)

A borrower types part of a title, author, or ISBN to narrow the list.

**Why this priority**: Essential once the catalog grows, but builds on browse.

**Independent Test**: Enter a query; only matching titles are shown.

**Acceptance Scenarios**:

1. **Given** the browse page, **When** the user types text matching a title name, author, or ISBN (case-insensitive), **Then** only matching titles are shown.
2. **Given** a query with no matches, **When** it is submitted, **Then** an empty-state message is shown.
3. **Given** an empty query, **When** browsing, **Then** all titles are listed.

### Edge Cases

- What happens with a very long or special-character query? → Treated as a literal substring; no error.
- What about a title with zero copies? → Shown as "Not available" (0 of 0).
- Do Borrowers see barcodes or shelf locations? → No; only availability counts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Any signed-in user (Borrower, Librarian, Administrator) MUST be able to browse titles with availability.
- **FR-002**: The system MUST show per-title availability as available-copy count over total-copy count, computed in real time (a copy counts as available only when its status is `available`).
- **FR-003**: Users MUST be able to search titles by a case-insensitive substring across name, author, and ISBN.
- **FR-004**: An empty query MUST return all titles; a non-matching query MUST return an empty result with a clear empty state.
- **FR-005**: The borrower-facing browse/search MUST NOT expose internal copy barcodes or exact locations.
- **FR-006**: Browsing/searching is read-only and MUST NOT allow catalog mutations.

### Key Entities *(reuses existing)*

- **Title** and **Copy** (from the catalog feature). This feature adds no new
  persistent entities; it provides a read/aggregate view.

## Success Criteria *(mandatory)*

- **SC-001**: A borrower can find a title by typing part of its name in under 15 seconds.
- **SC-002**: Availability shown matches the true count of `available` copies 100% of the time.
- **SC-003**: The browse list for a typical library (hundreds of titles) renders well under the constitution's 500ms query budget.
- **SC-004**: The borrower view never reveals barcodes or shelf locations.

## Assumptions

- Reuses the catalog (Title/Copy) data and the existing stack, auth, and roles.
- Availability is derived live from copy status; no denormalized counter in v1.
- Sorting defaults to title name; pagination is out of scope for v1 (hundreds of titles render fine).
- Reserving/holds and borrowing are separate later features; this is read-only discovery.
