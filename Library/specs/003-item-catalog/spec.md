# Feature Specification: Item / Catalog Management

**Feature Branch**: `003-item-catalog`

**Created**: 2026-07-20

**Status**: Implemented (US1, US2, US3) — 10 backend tests + 4 Playwright E2E passing; implements the real location copy-count for feature 002

**Input**: User description: "Item / catalog management — books/media with individual copies, ISBN, status, assignable to locations. Titles have one or more physical copies; each copy lives at a location and has a status and a barcode."

## Clarifications

Resolved during specification:

- **Model**: Two levels — a bibliographic **Title** (e.g., "Charlotte's Web" by E.B. White) with one or more physical **Copies**. Each copy has its own location, status, and barcode.
- **Identifiers**: ISBN is optional at the Title level. Each Copy has a barcode/accession number that is **auto-generated** but may be overridden manually; barcodes are unique.
- **Copy status**: `available`, `checked_out`, `lost`, `withdrawn`.
- **Required fields**: Title name is required (author, ISBN, media type optional). Each copy requires a location; status defaults to `available` and the barcode is auto-assigned.
- **Placement**: A copy may be placed at **any** location node (per the locations feature).
- **Management**: Administrators and Librarians manage the catalog (staff). Borrowers do not manage it (browsing/search is a separate feature).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Catalog a title with copies (Priority: P1) 🎯 MVP

A librarian adds a book to the catalog by entering its details (title, optionally
author/ISBN/media type) and then adds one or more physical copies, each placed at a
location. Every copy automatically receives a unique barcode.

**Why this priority**: Without titles and copies there is no inventory to manage,
search, or lend. This is the foundation for search (later) and borrowing (later),
and delivers immediate value: staff can record their holdings.

**Independent Test**: Add a title, add two copies at chosen locations, and confirm
both copies appear with unique barcodes and `available` status.

**Acceptance Scenarios**:

1. **Given** a signed-in Librarian or Administrator, **When** they create a title with a name, **Then** the title is saved (author/ISBN/media type optional).
2. **Given** an existing title, **When** they add a copy and choose a location, **Then** the copy is created at that location with status `available` and a unique auto-generated barcode.
3. **Given** a copy being added, **When** a barcode is entered manually, **Then** it is used if unique, otherwise the addition is refused.
4. **Given** the catalog, **When** a staff member views a title, **Then** its copies (with barcode, location, and status) are listed.
5. **Given** a title with no location chosen for a copy, **When** they try to add the copy, **Then** it is refused with a validation message.

---

### User Story 2 - Maintain titles and copies (Priority: P2)

Staff correct a title's details, move a copy to a different location, or change a
copy's status (e.g., mark a copy `lost` or `withdrawn`).

**Why this priority**: Real catalogs need upkeep, but it builds on US1.

**Independent Test**: Edit a title's author; move a copy to another location; mark a
copy `lost`; confirm each change and that it is audited.

**Acceptance Scenarios**:

1. **Given** an existing title, **When** a staff member edits its fields, **Then** the changes are saved and recorded in the audit log.
2. **Given** a copy, **When** a staff member moves it to a different location, **Then** the copy's location is updated.
3. **Given** an available copy, **When** a staff member marks it `lost` or `withdrawn`, **Then** the status changes and is recorded.
4. **Given** a copy that is `checked_out`, **When** a staff member attempts a status change that conflicts with an active loan (e.g., withdraw), **Then** it is refused (the loan must be resolved first — borrowing is a later feature).

---

### User Story 3 - Remove copies and titles (Priority: P3)

Staff remove a copy that is no longer held, or delete a title once it has no copies.

**Why this priority**: Housekeeping; depends on US1 and interacts with borrowing/locations.

**Independent Test**: Delete an available copy (succeeds); attempt to delete a
checked-out copy (refused); attempt to delete a title that still has copies
(refused); remove its copies then delete it (succeeds).

**Acceptance Scenarios**:

1. **Given** an `available` (or `lost`/`withdrawn`) copy, **When** a staff member deletes it, **Then** it is removed and the deletion is audited.
2. **Given** a `checked_out` copy, **When** a staff member tries to delete it, **Then** deletion is refused.
3. **Given** a title that still has copies, **When** a staff member tries to delete it, **Then** deletion is refused.
4. **Given** a title with no copies, **When** a staff member deletes it, **Then** it is removed and audited.

---

### Edge Cases

- What happens when a title name is empty/whitespace? → Refused with a validation message.
- What happens when a manually entered barcode duplicates an existing one? → Refused as a conflict.
- What happens when a copy's location is deleted? → The location cannot be deleted while it holds copies (enforced by the locations feature via the item count this feature provides).
- What happens to a copy's location if it is `withdrawn`? → The copy retains its record and location for history; it is no longer considered available.
- How are ISBNs validated? → ISBN is optional and stored as entered in v1 (format checking is out of scope); no uniqueness is enforced (multiple editions/titles may share none or reuse values).

## Requirements *(mandatory)*

### Functional Requirements

**Titles**

- **FR-001**: Staff (Administrator or Librarian) MUST be able to create a title with a required name and optional author, ISBN, and media type.
- **FR-002**: Staff MUST be able to view a list of titles and, for a title, its copies.
- **FR-003**: Staff MUST be able to edit a title's fields.
- **FR-004**: Staff MUST be able to delete a title only when it has no copies.

**Copies**

- **FR-005**: Staff MUST be able to add a copy to a title; each copy requires a location and defaults to status `available`.
- **FR-006**: The system MUST assign each copy a unique barcode automatically; a manually entered barcode MUST be accepted only if unique.
- **FR-007**: Staff MUST be able to move a copy to a different location (any location node).
- **FR-008**: Staff MUST be able to change a copy's status among `available`, `lost`, and `withdrawn`; the `checked_out` status is set/cleared by the borrowing feature, not manually.
- **FR-009**: The system MUST refuse a status change or deletion that conflicts with an active loan (a `checked_out` copy).
- **FR-010**: Staff MUST be able to delete a copy that is not `checked_out`.

**Integration & access**

- **FR-011**: The system MUST expose an accurate count of copies assigned to a given location (implementing the count the locations feature uses to guard deletion).
- **FR-012**: Only Administrators and Librarians may manage the catalog; Borrowers MUST be denied.
- **FR-013**: Every create, edit, move, status change, and delete (of titles and copies) MUST be recorded in the audit log with who/what/when/why.

### Key Entities *(include if feature involves data)*

- **Title**: A bibliographic record. Attributes: id, name (required), author, isbn, media_type (all optional), timestamps, creator. Has zero-or-more Copies.
- **Copy**: A physical item. Attributes: id, title (ref), barcode (unique), location (ref to a Location), status (`available`/`checked_out`/`lost`/`withdrawn`), optional condition, timestamps, creator.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A librarian can add a title with three copies (at chosen locations) in under 2 minutes.
- **SC-002**: 100% of copies have a unique barcode; duplicate barcodes are never persisted.
- **SC-003**: The location copy-count is accurate 100% of the time, so a location holding copies can never be deleted.
- **SC-004**: A `checked_out` copy is never deleted and its status is never manually changed to a conflicting state.
- **SC-005**: 100% of title/copy create/edit/move/status/delete actions produce an audit log entry.

## Assumptions

- Browsing and searching the catalog by borrowers is a separate feature (F5); this feature provides the staff-facing management and the data model both rely on.
- Borrowing/returning (setting `checked_out`) is a separate feature (F6); here `checked_out` is treated as a state the catalog must respect but does not itself create.
- Auto-generated barcodes use a simple unique scheme (e.g., a sequential accession number with a prefix); the exact format is an implementation detail and configurable.
- ISBN is free-form in v1 (no format validation or uniqueness).
- Reuses the existing stack (FastAPI + SQLAlchemy + React/MUI), auth, roles, staff guards, locations, and audit infrastructure from features 001–002.
- The location copy-count (FR-011) replaces the temporary `item_count` hook (which returned 0) introduced in the locations feature.
