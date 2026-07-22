# Phase 0 Research: Inventory Location Management

**Feature**: Inventory Location Management
**Date**: 2026-07-20

## Context

The feature adds a flexible, arbitrary-depth location tree managed by staff, at a
small scale (hundreds of nodes). It must reuse the feature-001 stack and honor the
Lightweight & Low-Maintenance principle (no unjustified dependencies or complexity).

## Decision 1 — Tree storage: adjacency list (nullable parent_id)

**Decision**: Store the tree as an **adjacency list** — each `Location` row has a
nullable `parent_id` foreign key to another `Location`. Roots have `parent_id = NULL`.

**Rationale**:
- Simplest possible model; trivial to create and to reparent (a single field update).
- At library scale (hundreds of nodes), the entire tree loads in one query and is
  assembled in memory cheaply — no need for specialized structures.
- Maps directly to SQLAlchemy self-referential relationships and ports cleanly to
  PostgreSQL later.

**Alternatives considered**:
- *Nested set / materialized path / closure table*: optimize deep-subtree queries
  at large scale, but add write complexity and bookkeeping. Rejected as
  over-engineering for this scale (Principle VII).

## Decision 2 — Cycle prevention on move

**Decision**: Before reparenting a node, verify the proposed new parent is neither
the node itself nor one of its descendants. Implemented by walking descendants of
the moved node (or walking ancestors of the target parent) using the in-memory tree.

**Rationale**: O(n) at this scale is negligible; keeps the model simple and correct
(Data Integrity). No database-level recursion needed.

## Decision 3 — Sibling-name uniqueness

**Decision**: Enforce unique names among siblings (same parent), case-insensitively,
in the service layer using a normalized-name check. Reuse the username-style
normalization (trim + case-fold) for consistency.

**Rationale**: A pure database unique constraint on `(parent_id, name_normalized)`
does not catch duplicate **root** names because SQL treats `NULL` parents as
distinct. An application-level check covers both roots and children uniformly; a
supporting non-unique index on `(parent_id, name_normalized)` keeps lookups fast.

**Alternatives considered**:
- *DB unique constraint only*: misses the NULL-parent (root) case. Kept as a
  secondary safeguard for children, but the authoritative check is in the service.

## Decision 4 — Delete safety (block when non-empty)

**Decision**: Refuse deletion when a location has any child locations or any items.
Items are a future feature; the service calls a `count_items(location_id)` hook that
returns 0 until the catalog feature lands, so the rule is already wired and testable.

**Rationale**: Prevents orphaned inventory (Data Integrity). The hook keeps the
contract stable when items arrive.

## Decision 5 — Frontend tree component (no new dependency)

**Decision**: Build a small **custom recursive tree** using MUI `List`, `Collapse`,
and `IconButton` for expand/collapse and inline actions, rather than adding a
dedicated tree library (e.g., `@mui/x-tree-view`).

**Rationale**: The interaction set is modest (expand, add child, rename, move,
delete). A ~100-line component avoids a new dependency and bundle weight,
satisfying the Lightweight principle while keeping accessibility under our control.

**Alternatives considered**:
- *`@mui/x-tree-view`*: richer, but a new dependency for functionality we can meet
  simply. Reconsider later if the interaction grows (drag-and-drop, virtualization).

## Access control

- Location endpoints are **staff-only** (Administrator or Librarian). This
  introduces a `require_staff` dependency alongside the existing `require_admin`;
  Borrowers are denied. Mutations require CSRF and are audited.

## Testing approach

- **Backend**: pytest for tree assembly, create/rename/move, cycle rejection,
  sibling-uniqueness, and delete-guard behavior.
- **E2E**: Playwright drives the staff tree UI (build → rename → move → delete).

## Summary of choices

| Concern            | Choice                                             |
|--------------------|----------------------------------------------------|
| Tree storage       | Adjacency list (nullable `parent_id`)              |
| Read strategy      | One query, assemble tree in memory                 |
| Cycle prevention   | Descendant/ancestor check before reparent          |
| Sibling uniqueness | Service-level normalized check (+ supporting index)|
| Delete safety      | Block if children or items; `count_items` hook     |
| Tree UI            | Custom recursive MUI component (no new dep)        |
| Access             | Staff-only (`require_staff`), CSRF, audited        |
