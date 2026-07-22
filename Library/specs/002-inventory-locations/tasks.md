---
description: "Task list for Inventory Location Management"
---

# Tasks: Inventory Location Management

**Input**: Design documents from `specs/002-inventory-locations/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/locations-api.md

**Tests**: Included and REQUIRED (constitution Principle V, Test-First).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3

## Path Conventions

Extends the existing app (per plan.md): `backend/src/`, `frontend/src/`, `e2e/tests/`.

---

## Phase 1: Setup

- [ ] T001 Confirm no new dependencies are required (reuse existing stack); note the new `locations` table is created by `create_all`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure all location stories depend on.

- [ ] T002 Create the `Location` model (adjacency list: id, name, name_normalized, type_label, nullable parent_id, timestamps, created_by) in `backend/src/models/location.py`, register it in `backend/src/models/__init__.py`, and add a supporting index on `(parent_id, name_normalized)`
- [ ] T003 [P] Add a `require_staff` (Administrator or Librarian) read guard and `require_staff_write` (staff + CSRF) write guard in `backend/src/api/deps.py`
- [ ] T004 [P] Add a **dedicated location-name** helper (trim, collapse repeated spaces, non-empty, case-fold; allowed chars: letters, digits, spaces, `. _ -`) — do NOT reuse the username validator (usernames forbid spaces) — in `backend/src/core/locations_name.py`
- [ ] T005 Create the locations service skeleton with a stable-signature `item_count(location_id)` hook returning 0 (until the catalog feature) and a configurable max-depth check (default 10) in `backend/src/services/locations.py`

**Checkpoint**: Model, guards, and service scaffold ready.

---

## Phase 3: User Story 1 — Build a location structure (Priority: P1) 🎯 MVP

**Goal**: Staff create root and nested locations and view the tree.

**Independent Test**: Create root → child → grandchild; GET the tree and confirm nesting.

### Tests for User Story 1 ⚠️ (write first, must fail)

- [ ] T006 [P] [US1] Contract tests for `GET /api/v1/locations` and `POST /api/v1/locations` (root + child, staff-only, 403 for borrower) in `backend/tests/integration/test_locations.py`
- [ ] T007 [P] [US1] Unit/integration tests for tree assembly and sibling-name uniqueness (roots and children, case-insensitive) in `backend/tests/integration/test_locations.py`
- [ ] T008 [P] [US1] Playwright E2E: staff builds Room → Shelf → Row and sees the tree in `e2e/tests/locations.spec.ts`

### Implementation for User Story 1

- [ ] T009 [US1] Location service: `list_tree` (one query + in-memory assembly), `create` (root/child, sibling-uniqueness, parent existence), with audit logging, in `backend/src/services/locations.py`
- [ ] T010 [P] [US1] Pydantic schemas: `LocationNode` (recursive tree), `CreateLocation` in `backend/src/schemas/locations.py`
- [ ] T011 [US1] Locations router: `GET /locations`, `POST /locations` (staff-only, CSRF on create) in `backend/src/api/locations.py`; wire into `backend/src/main.py`
- [ ] T012 [P] [US1] Recursive tree component with proper **ARIA tree semantics** (`role="tree"`/`"treeitem"`, `aria-expanded`, arrow-key navigation) and expand/collapse, add-child, add-root in `frontend/src/components/LocationTree.tsx`
- [ ] T013 [US1] Locations page (load tree, create root/child dialog) in `frontend/src/pages/Locations.tsx`; add API methods in `frontend/src/services/api.ts`
- [ ] T014 [US1] Add a staff-only `/locations` route + nav entry (Home card + AppLayout link) in `frontend/src/App.tsx`, `frontend/src/pages/Home.tsx`, `frontend/src/components/AppLayout.tsx`

**Checkpoint**: US1 fully functional — staff can build and view the tree (MVP).

---

## Phase 4: User Story 2 — Reorganize locations (Priority: P2)

**Goal**: Rename and move locations (subtree moves; no cycles).

**Independent Test**: Rename a node; move a subtree under a new parent; attempt an illegal move (rejected).

### Tests for User Story 2 ⚠️ (write first, must fail)

- [ ] T015 [P] [US2] Contract/integration tests for `PATCH /locations/{id}` (rename, duplicate-sibling 409) and `PATCH /locations/{id}/move` (subtree move, cycle 409, root move) in `backend/tests/integration/test_locations.py`
- [ ] T016 [P] [US2] Playwright E2E: rename a location and move a subtree in `e2e/tests/locations.spec.ts`

### Implementation for User Story 2

- [ ] T017 [US2] Service: `rename` (uniqueness) and `move` (cycle check via descendant walk, destination uniqueness), with audit, in `backend/src/services/locations.py`
- [ ] T018 [P] [US2] Schemas: `UpdateLocation`, `MoveLocation` in `backend/src/schemas/locations.py`
- [ ] T019 [US2] Router: `PATCH /locations/{id}` and `PATCH /locations/{id}/move` (staff + CSRF) in `backend/src/api/locations.py`
- [ ] T020 [US2] UI: rename dialog + move dialog (parent picker) in `frontend/src/pages/Locations.tsx` / `LocationTree.tsx`; add API methods

**Checkpoint**: US1 and US2 both work.

---

## Phase 5: User Story 3 — Safe deletion (Priority: P3)

**Goal**: Delete only empty locations (no children, no items).

**Independent Test**: Delete non-empty → refused; empty → succeeds.

### Tests for User Story 3 ⚠️ (write first, must fail)

- [ ] T021 [P] [US3] Integration tests for `DELETE /locations/{id}`: refused with children (409), refused with items (409, via mocked `item_count`), succeeds when empty (204) in `backend/tests/integration/test_locations.py`
- [ ] T022 [P] [US3] Playwright E2E: delete blocked for non-empty, allowed for empty in `e2e/tests/locations.spec.ts`

### Implementation for User Story 3

- [ ] T023 [US3] Service: `delete` with empty-check (children + `item_count`), audit, in `backend/src/services/locations.py`
- [ ] T024 [US3] Router: `DELETE /locations/{id}` (staff + CSRF) in `backend/src/api/locations.py`
- [ ] T025 [US3] UI: delete action with confirmation and clear blocked-message handling in `frontend/src/pages/Locations.tsx` / `LocationTree.tsx`

**Checkpoint**: All three stories independently functional.

---

## Phase 6: Polish & Cross-Cutting

- [ ] T026 [P] Verify audit entries for create/rename/move/delete in `backend/tests/integration/test_locations.py`
- [ ] T027 [P] Accessibility pass: axe check on the Locations page + verify the tree's ARIA roles and full keyboard navigation (arrow keys expand/collapse/move focus) in `e2e/tests/locations.spec.ts`
- [ ] T028 Confirm ≥80% coverage for the new backend code; fill gaps
- [ ] T029 Run quickstart.md validation end-to-end
- [ ] T030 [P] Security review: staff-only guards, CSRF on all mutations, transactional integrity, no cycles/orphans
- [ ] T031 [P] Lightweight render smoke test: seed a few hundred nodes and confirm the tree endpoint + page render within budget (SC-002) in `backend/tests/integration/test_locations.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** blocks all stories.
- **US1 (P1)** is the MVP; **US2** and **US3** build on the shared model/service.
- Recommended order: US1 → US2 → US3, then Polish.

### Within Each User Story

- Tests written and failing BEFORE implementation (Test-First).
- Model → service → schemas → router → frontend.

### Parallel Opportunities

- `[P]` tasks touch different files and can run together (e.g., schemas vs. tree component vs. tests).

---

## Implementation Strategy

**MVP first**: Phase 1 → Phase 2 → Phase 3 (US1) yields a working, demonstrable
location tree. Then add reorganization (US2) and safe deletion (US3), finishing
with the Polish phase.
