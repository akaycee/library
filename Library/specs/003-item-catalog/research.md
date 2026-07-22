# Phase 0 Research: Item / Catalog Management

**Feature**: Item / Catalog Management
**Date**: 2026-07-20

## Context

Add a two-level catalog (Titles → Copies) at small scale (hundreds of records),
reusing the features 001–002 stack and honoring the Lightweight principle.

## Decision 1 — Two tables: Title and Copy

**Decision**: `titles` (bibliographic) and `copies` (physical), with `copies.title_id`
→ `titles.id` and `copies.location_id` → `locations.id`.

**Rationale**: Matches the domain (a title owns many copies), avoids duplicating
bibliographic metadata across copies, and cleanly supports future borrowing (loans
attach to a copy).

**Alternatives considered**:
- *Flat items*: simpler schema but duplicates title/author on every copy and
  complicates future de-duplication and search. Rejected per the user's choice.

## Decision 2 — Barcode generation: sequential accession number

**Decision**: Auto-generate a barcode as a zero-padded **sequential accession
number** with a short prefix (e.g., `LIB-000123`). A manually entered barcode is
accepted only if unique. Uniqueness is enforced by a DB unique constraint plus a
service check that returns a friendly conflict.

**Rationale**: Human-readable, collision-free, trivial to implement, and works
offline. The next number is derived from a max/counter at creation time inside the
transaction.

**Alternatives considered**:
- *Random/UUID barcodes*: opaque and unfriendly for staff reading labels aloud.
- *External barcode service*: violates offline/local and Lightweight principles.

## Decision 3 — Copy status model

**Decision**: `CopyStatus` enum = `available` | `checked_out` | `lost` | `withdrawn`.
Staff may set `available`/`lost`/`withdrawn`; `checked_out` is set/cleared only by
the future borrowing feature. Status changes and deletions that conflict with a
`checked_out` copy are refused.

**Rationale**: Covers normal operation now while reserving loan transitions for F6,
preventing catalog edits from corrupting an active loan (Data Integrity).

## Decision 4 — Location copy-count (replaces the F3 hook)

**Decision**: Implement `count copies where location_id = X` and wire it into the
locations service's `item_count`, so a location holding copies cannot be deleted.

**Rationale**: Fulfills the forward dependency documented in feature 002 and keeps
the delete-safety guarantee intact end to end.

## Decision 5 — Delete safety

**Decision**: Refuse deleting a **title** that still has copies; refuse deleting a
**copy** that is `checked_out`. Otherwise deletion is allowed and audited.

**Rationale**: Prevents orphaned copies and protects active loans.

## Decision 6 — Frontend: titles list + title detail, reuse location picker

**Decision**: A `Catalog` page (titles list + add title) and a `TitleDetail` page
(edit fields; manage copies: add/move/status/delete). Copy location selection reuses
a flattened-tree **LocationPicker** derived from the locations feature.

**Rationale**: Familiar master/detail UX; reuses existing tree data with no new
dependency (Lightweight).

## Access control

- All catalog endpoints are staff-only (`require_staff` / `require_staff_write`);
  Borrowers denied. Mutations require CSRF and are audited.

## Testing approach

- **Backend**: pytest for barcode uniqueness, copy status/delete guards, title
  delete-when-empty, and the location copy-count (location deletion blocked).
- **E2E**: Playwright drives add-title → add-copies → move → status → delete flows,
  plus an axe accessibility check on the catalog pages.

## Summary of choices

| Concern         | Choice                                                   |
|-----------------|----------------------------------------------------------|
| Schema          | `titles` + `copies` (FK to title and location)           |
| Barcode         | Sequential accession `LIB-000123`; manual if unique      |
| Status          | available / checked_out / lost / withdrawn               |
| Location count  | Real `count copies by location` wired into F3 guard      |
| Delete safety   | Title blocked if has copies; copy blocked if checked_out |
| UI              | Catalog list + Title detail; reused LocationPicker       |
| Access          | Staff-only, CSRF, audited                                |
