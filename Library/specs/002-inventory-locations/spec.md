# Feature Specification: Inventory Location Management

**Feature Branch**: `002-inventory-locations`

**Created**: 2026-07-20

**Status**: Implemented (US1, US2, US3) — 11 backend tests + 4 Playwright E2E passing; reuses feature-001 auth/audit infrastructure

**Input**: User description: "The inventory location can be dynamic — rooms, shelves, rows, one or two of them, or a completely different mechanism. Allow the librarian or administrator to create an inventory location structure to be filled in with items later."

## Clarifications

Resolved during specification:

- **Structure**: An arbitrary nested tree of location nodes — any depth, each node freely named, with multiple independent roots allowed (a "forest").
- **Item placement**: Items (added later in the catalog feature) may be placed at **any** location node, not only the deepest ones.
- **Who manages**: Both Administrators and Librarians can create and edit locations.
- **Delete safety**: Deleting a location is blocked while it still has child locations or items.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build a location structure (Priority: P1) 🎯 MVP

A librarian sets up the library's physical layout by creating locations and nesting
them — for example a "Main Room" containing "Shelf A", which contains "Row 1".
Each location has a name and an optional type label (Room, Shelf, Row, or anything
custom). The structure can be as shallow or as deep as the library needs.

**Why this priority**: Nothing can be shelved or organized until locations exist.
This is the foundation the catalog (items) will build on, and it delivers standalone
value: staff can model their real space immediately.

**Independent Test**: Create a root location, add a child under it, then a
grandchild; view the resulting tree and confirm the hierarchy and names.

**Acceptance Scenarios**:

1. **Given** a signed-in Librarian or Administrator, **When** they create a location with a name and no parent, **Then** it appears as a new root location.
2. **Given** an existing location, **When** they create a child location under it, **Then** the child appears nested beneath the parent.
3. **Given** a location, **When** they add an optional type label (e.g., "Shelf"), **Then** the label is saved and shown with the location.
4. **Given** a parent location, **When** they try to create a second child with the same name under that same parent, **Then** it is refused as a duplicate.
5. **Given** the location tree, **When** a staff member opens the locations view, **Then** the full nested structure is displayed.

---

### User Story 2 - Reorganize locations (Priority: P2)

As the library changes, staff rename a location or move a whole location (with its
contents) to a different parent — for example moving "Shelf A" from "Main Room" to
"Annex".

**Why this priority**: Real libraries rearrange. Editing builds on US1 but is not
required to prove the core structure works.

**Independent Test**: Rename a location and confirm the new name; move a location
under a different parent and confirm the subtree moved with it.

**Acceptance Scenarios**:

1. **Given** an existing location, **When** a staff member renames it, **Then** the new name is shown and the change is recorded in the audit log.
2. **Given** a location with children, **When** a staff member moves it under a different parent, **Then** the entire subtree moves with it.
3. **Given** a location, **When** a staff member attempts to move it under itself or one of its own descendants, **Then** the move is refused (no cycles).
4. **Given** a move that would create a duplicate name among the destination's children, **When** it is attempted, **Then** it is refused.

---

### User Story 3 - Safe deletion (Priority: P3)

A staff member removes a location that is no longer used. To protect inventory
integrity, a location can only be deleted once it is empty — it has no child
locations and no items.

**Why this priority**: Important for tidiness and correctness but depends on US1
(and, for the item check, on the future catalog feature).

**Independent Test**: Attempt to delete a location that has a child (refused);
remove the child, then delete the now-empty location (succeeds).

**Acceptance Scenarios**:

1. **Given** a location with one or more child locations, **When** a staff member tries to delete it, **Then** deletion is refused with a clear message.
2. **Given** a location that holds one or more items, **When** a staff member tries to delete it, **Then** deletion is refused with a clear message.
3. **Given** an empty location (no children, no items), **When** a staff member deletes it, **Then** it is removed and the deletion is recorded in the audit log.

---

### Edge Cases

- What happens when a location name is empty or only whitespace? → Creation/rename is refused with a validation message.
- What happens with very deep nesting? → Arbitrary depth is supported up to a configurable maximum (default 10 levels) to prevent pathological input; within that, trees remain usable.
- How are duplicate names handled? → Names must be unique among siblings (same parent); the same name may exist under different parents.
- What happens when two staff edit the same location concurrently? → Last write wins for names; structural moves are validated against the current tree to avoid cycles.
- Can a borrower see or change locations? → No; location management and the raw location tree are staff-only in this feature.

## Requirements *(mandatory)*

### Functional Requirements

**Structure & creation**

- **FR-001**: Staff (Administrator or Librarian) MUST be able to create a location with a required name and an optional free-text type label (e.g., Room, Shelf, Row, or custom).
- **FR-002**: A location MUST be creatable either as a root (no parent) or as a child of an existing location; multiple roots are allowed.
- **FR-003**: The location structure MUST support arbitrary nesting depth.
- **FR-004**: Location names MUST be unique among siblings sharing the same parent (case-insensitively); the same name MAY appear under different parents.
- **FR-005**: Staff MUST be able to view the full location tree.

**Reorganization**

- **FR-006**: Staff MUST be able to rename a location.
- **FR-007**: Staff MUST be able to move a location (with its entire subtree) to a different parent or to root.
- **FR-008**: The system MUST prevent moves that would create a cycle (a location cannot become a descendant of itself).
- **FR-009**: Renames and moves MUST respect the sibling-uniqueness rule (FR-004).

**Deletion**

- **FR-010**: The system MUST refuse to delete a location that has any child locations.
- **FR-011**: The system MUST refuse to delete a location that has any items assigned to it.
- **FR-012**: Staff MUST be able to delete a location that has no children and no items.

**Access & auditability**

- **FR-013**: Only Administrators and Librarians may view or manage locations; Borrowers MUST be denied.
- **FR-014**: Every create, rename, move, and delete MUST be recorded in the audit log with who, what, when, and why (per constitution).

### Key Entities *(include if feature involves data)*

- **Location**: A node in the location tree. Attributes: unique id, name, optional type label, optional parent (null for roots), timestamps, and creator. Relationships: a Location has zero or one parent and zero-or-more children; items (future feature) reference a Location.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A librarian can create a three-level location (e.g., Room → Shelf → Row) in under 1 minute.
- **SC-002**: The locations view renders the full tree for a typical library (hundreds of nodes) without noticeable delay (well under the constitution's 500ms budget for standard queries).
- **SC-003**: 100% of location create/rename/move/delete actions produce an audit log entry.
- **SC-004**: Deletion is refused in 100% of cases where the location has children or items; never leaves an orphaned item.
- **SC-005**: A staff member can locate and move a subtree in under 30 seconds on first attempt.

## Assumptions

- Locations are staff-facing organizational structures; borrowers interact with the catalog (future feature), not the raw location tree.
- The "item" relationship is defined here but enforced fully once the catalog feature exists; until then, the item check (FR-011) treats every location as having zero items.
- Type labels (Room/Shelf/Row/…) are free text for flexibility; no fixed vocabulary is imposed in v1.
- Location names allow letters, digits, spaces, and `. _ -` (e.g., "Main Room", "Shelf A-2"); they are trimmed and collapsed of repeated spaces. This is intentionally broader than usernames (which forbid spaces), so the username validator is NOT reused for names.
- Sibling-name uniqueness uses the same normalization *approach* as usernames — trim + Unicode case-fold — applied by a dedicated location-name helper.
- Nesting depth is limited to a configurable maximum (default 10 levels).
- Reuses the existing stack (FastAPI + SQLAlchemy + React/MUI), auth, roles, and audit infrastructure from feature 001.
