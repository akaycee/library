# Phase 1 Data Model: Inventory Location Management

**Feature**: Inventory Location Management
**Date**: 2026-07-20

Implemented with SQLAlchemy 2.x; created via `create_all` (consistent with feature
001). Portable to PostgreSQL as a tested migration later.

## Entities

### Location

A node in the location tree (adjacency list).

| Field           | Type        | Notes |
|-----------------|-------------|-------|
| id              | UUID/str PK | Primary key |
| name            | string      | Display name as entered (trimmed) |
| name_normalized | string      | Trimmed + case-folded; used for sibling-uniqueness checks |
| type_label      | string/null | Optional free-text label (e.g., "Room", "Shelf", "Row") |
| parent_id       | FK → Location, nullable | Null for root locations |
| created_at      | datetime    | UTC |
| updated_at      | datetime    | UTC |
| created_by      | FK → User, nullable | Who created it |

**Relationships**:
- `Location.parent` → zero or one `Location`.
- `Location.children` → zero or more `Location` (ordered by name for display).
- (Future) `Item.location_id` → `Location`; drives the delete-guard item check.

**Rules**:
- `name` is required and non-empty after trimming (FR-001). Allowed characters:
  letters, digits, spaces, and `. _ -` (broader than usernames, which forbid
  spaces) — so the username validator is NOT reused; a dedicated location-name
  helper does trim + repeated-space collapse + Unicode case-fold for the
  normalized form.
- `name_normalized` MUST be unique among siblings sharing the same `parent_id`,
  including among roots (`parent_id IS NULL`) — enforced in the service (FR-004).
- A location MAY be a root (`parent_id = NULL`) or nested up to a configurable
  maximum depth (default 10 levels) (FR-002, FR-003).
- Moving a location sets a new `parent_id`; the target MUST NOT be the node itself
  or any of its descendants (FR-008).
- Deletion is refused while the location has any child locations (FR-010) or any
  items (FR-011); allowed only when empty (FR-012).

## Supporting index

- Non-unique index on `(parent_id, name_normalized)` to speed sibling lookups. The
  authoritative uniqueness check is in the service (covers the NULL-parent case).

## Derived / computed

- **Tree**: assembled in memory from a single `SELECT * FROM locations` — group by
  `parent_id`, attach children to parents, return roots.
- **Ancestry/descendants**: computed in memory for cycle checks and breadcrumbs.
- **item_count(location_id)**: a service hook with a **stable signature** returning
  0 until the catalog feature exists; then it counts items assigned to the
  location. Keeping the signature fixed avoids churn when items arrive.

## Enumerations

- None. `type_label` is intentionally free text (no fixed vocabulary in v1).

## Audit

- Create, rename, move, and delete each write an append-only `AuditLogEntry`
  (actor, action e.g. `location.create`/`location.rename`/`location.move`/
  `location.delete`, target, reason) — reusing feature-001 audit infrastructure.
