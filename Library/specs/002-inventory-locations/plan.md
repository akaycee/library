# Implementation Plan: Inventory Location Management

**Branch**: `002-inventory-locations` | **Date**: 2026-07-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-inventory-locations/spec.md`

## Summary

Add a flexible, staff-managed **location tree** to the existing application: an
arbitrary-depth hierarchy of freely-named location nodes (multiple roots allowed),
with create / rename / move / delete operations, cycle protection, sibling-name
uniqueness, block-delete-when-non-empty, and full audit logging. It reuses the
feature-001 stack (FastAPI + SQLAlchemy + SQLite/SQLCipher backend; React + Vite +
MUI frontend) and its auth, roles, session, CSRF, and audit infrastructure.

The tree is stored as an **adjacency list** (each node has a nullable `parent_id`),
which is the simplest model that meets the requirement at library scale (hundreds
of nodes) — consistent with the Lightweight principle. The full tree is loaded in
one query and assembled in memory.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x / React 18 (frontend)

**Primary Dependencies**: existing — FastAPI, SQLAlchemy 2.x, Pydantic v2, MUI. No new dependencies (the tree UI is a small custom recursive component using MUI `List` + `Collapse`, avoiding a heavyweight tree library).

**Storage**: New `locations` table (adjacency list) via SQLAlchemy; created by `create_all` on startup, consistent with feature 001.

**Testing**: pytest + httpx (backend), Playwright (E2E).

**Target Platform**: Same single-process local deployment as feature 001.

**Project Type**: Web application (extends the existing backend + frontend).

**Performance Goals**: Tree list well under the 500ms budget for hundreds of nodes.

**Constraints**: Staff-only (Administrator/Librarian); all mutations audited and CSRF-protected; no cycles; deletion blocked when non-empty.

**Scale/Scope**: Hundreds of location nodes; a handful of concurrent staff.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Data Integrity First**: PASS — all mutations run in a transaction; moves are validated against the current tree to prevent cycles; deletion is refused while children/items exist, so no orphans.
- **II. Complete Audit Trail**: PASS — create/rename/move/delete each write an append-only audit entry with who/what/when/why.
- **III. Role-Based Access Control**: PASS — a new `require_staff` guard restricts all location endpoints to Administrator or Librarian; Borrowers are denied.
- **IV. API-First Design**: PASS — every capability is exposed via the versioned `/api/v1/locations` API with Pydantic validation before the UI uses it.
- **V. Test-First**: PASS — pytest covers tree building, cycle/uniqueness rules, and delete safety; Playwright covers the staff tree UI.
- **VI. Ease of Use**: PASS — a clear MUI tree with inline add/rename/move/delete and forgiving, explicit error messages.
- **VII. Lightweight & Low-Maintenance**: PASS — adjacency list + in-memory assembly; a small custom tree component; no new dependencies or services.

No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/002-inventory-locations/
├── plan.md              # This file
├── research.md          # Phase 0 — tree-model decision & alternatives
├── data-model.md        # Phase 1 — Location entity & rules
├── quickstart.md        # Phase 1 — how to try it
├── contracts/
│   └── locations-api.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Created later by /speckit.tasks
```

### Source Code (extends the existing app)

```text
backend/
├── src/
│   ├── models/location.py       # NEW — Location (adjacency list)
│   ├── schemas/locations.py     # NEW — create/rename/move + tree views
│   ├── services/locations.py    # NEW — tree build, cycle/uniqueness, delete guard, audit
│   ├── api/locations.py         # NEW — /api/v1/locations router (staff-only)
│   └── api/deps.py              # UPDATED — add require_staff / require_staff_write
└── tests/integration/test_locations.py   # NEW

frontend/
├── src/
│   ├── pages/Locations.tsx      # NEW — location management page
│   ├── components/LocationTree.tsx  # NEW — recursive MUI tree
│   └── services/api.ts          # UPDATED — location methods
└── (App.tsx, Home.tsx, AppLayout.tsx UPDATED — staff route + nav)

e2e/
└── tests/locations.spec.ts      # NEW — build/rename/move/delete flows
```

**Structure Decision**: Extend the existing web app in place. Locations are a new
vertical slice (model → service → router → UI) mirroring the structure established
in feature 001, so it stays consistent and independently testable.

## Complexity Tracking

No constitution violations — section intentionally empty.
