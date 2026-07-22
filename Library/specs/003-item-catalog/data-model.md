# Phase 1 Data Model: Item / Catalog Management

**Feature**: Item / Catalog Management
**Date**: 2026-07-20

Implemented with SQLAlchemy 2.x; created via `create_all`. Reuses the `locations`
table from feature 002.

## Entities

### Title

A bibliographic record.

| Field       | Type        | Notes |
|-------------|-------------|-------|
| id          | UUID/str PK | |
| name        | string      | Required, trimmed, non-empty |
| author      | string/null | Optional |
| isbn        | string/null | Optional, free-form in v1 (no format/uniqueness) |
| media_type  | string/null | Optional free text (e.g., Book, DVD, Magazine) |
| created_by  | FK → User, null | |
| created_at  | datetime    | UTC |
| updated_at  | datetime    | UTC |

**Rules**:
- `name` required and non-empty after trimming (FR-001).
- A title may be deleted only when it has no copies (FR-004).

### Copy

A physical item belonging to a title.

| Field       | Type        | Notes |
|-------------|-------------|-------|
| id          | UUID/str PK | |
| title_id    | FK → Title  | Required |
| barcode     | string      | **Unique**; auto-generated (e.g., `LIB-000123`) or manual-if-unique |
| location_id | FK → Location | Required — where the copy lives |
| status      | enum        | `available` \| `checked_out` \| `lost` \| `withdrawn` |
| condition   | string/null | Optional free text |
| created_by  | FK → User, null | |
| created_at  | datetime    | UTC |
| updated_at  | datetime    | UTC |

**Rules**:
- `location_id` required at creation; status defaults to `available` (FR-005).
- `barcode` is unique (DB constraint + service check); auto-assigned as a
  sequential accession number unless a unique manual value is supplied (FR-006).
- Staff may set status to `available`/`lost`/`withdrawn`; `checked_out` is owned by
  the borrowing feature (FR-008).
- A `checked_out` copy MUST NOT be deleted or manually status-changed into a
  conflicting state (FR-009, FR-010).

## Enumerations

- **CopyStatus**: `available` | `checked_out` | `lost` | `withdrawn` (added to
  `models/base.py`).

## Relationships

- `Title (1) → (many) Copy`
- `Copy (many) → (1) Location` (feature 002)
- (Future) `Loan (1) → (1) Copy` in the borrowing feature.

## Barcode generation

- On copy creation without a manual barcode, generate the next sequential
  accession number inside the transaction: prefix + zero-padded counter derived
  from the current maximum. Retried/guarded by the unique constraint.

## Location integration

- Implement `count copies where location_id = X`; wire it into the locations
  service's `item_count(db, location_id)` so deleting a location that holds copies
  is refused (fulfills feature 002 FR-011).

## Audit

- Create/edit/move/status/delete of titles and copies each write an append-only
  `AuditLogEntry` (actor, action e.g. `title.create`/`copy.create`/`copy.move`/
  `copy.status`/`copy.delete`, target, reason).
