---
description: "Task list for Item / Catalog Management"
---

# Tasks: Item / Catalog Management

**Input**: Design documents from `specs/003-item-catalog/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/catalog-api.md

**Tests**: Included and REQUIRED (constitution Principle V, Test-First).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3

## Path Conventions

Extends the existing app: `backend/src/`, `frontend/src/`, `e2e/tests/`.

---

## Phase 1: Setup

- [ ] T001 Confirm no new dependencies; note new `titles` and `copies` tables are created by `create_all`.

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T002 Add `CopyStatus` enum (`available`/`checked_out`/`lost`/`withdrawn`) in `backend/src/models/base.py`
- [ ] T003 Create the `Title` model in `backend/src/models/title.py` and the `Copy` model (unique `barcode`, `title_id`, `location_id`, `status`, `condition`) in `backend/src/models/copy.py`; register both in `backend/src/models/__init__.py`
- [ ] T004 Create the catalog service skeleton with a barcode generator (sequential accession `LIB-000123`, unique) that **retries on the unique-constraint violation** (regenerates the next number) in `backend/src/services/catalog.py`
- [ ] T005 Implement the real location copy-count and wire it into `item_count` in `backend/src/services/locations.py` (replaces the temporary 0 hook)

**Checkpoint**: Models, enum, barcode generator, and location count ready.

---

## Phase 3: User Story 1 — Catalog a title with copies (Priority: P1) 🎯 MVP

**Goal**: Staff add a title and its copies (each at a location, auto-barcode) and view them.

**Independent Test**: Add a title, add two copies at locations, confirm unique barcodes + `available`.

### Tests for User Story 1 ⚠️ (write first, must fail)

- [ ] T006 [P] [US1] Contract tests for `POST/GET /titles`, `GET /titles/{id}`, `POST /titles/{id}/copies` (staff-only, 403 borrower) in `backend/tests/integration/test_catalog.py`
- [ ] T007 [P] [US1] Tests for barcode auto-generation + uniqueness (auto and manual-duplicate 409) and copy requires a location (422) in `backend/tests/integration/test_catalog.py`
- [ ] T008 [P] [US1] Playwright E2E: add a title, add two copies at locations, see barcodes in `e2e/tests/catalog.spec.ts`

### Implementation for User Story 1

- [ ] T009 [US1] Catalog service: `create_title`, `list_titles` (with copy_count), `get_title` (with copies + each copy's **location name/path** via a parent-walk helper), `add_copy` (location required, barcode auto/manual-unique with retry), with audit, in `backend/src/services/catalog.py`
- [ ] T010 [P] [US1] Pydantic schemas: `TitleCreate`, `TitleView`, `TitleDetail`, `CopyCreate`, `CopyView` (incl. `location_name`/`location_path`) in `backend/src/schemas/catalog.py`
- [ ] T011 [US1] Catalog router: `GET/POST /titles`, `GET /titles/{id}`, `POST /titles/{id}/copies` (staff + CSRF) in `backend/src/api/catalog.py`; wire into `backend/src/main.py`
- [ ] T012 [P] [US1] LocationPicker component (flattened location tree → select) in `frontend/src/components/LocationPicker.tsx`
- [ ] T013 [US1] Catalog page (titles list + add title) in `frontend/src/pages/Catalog.tsx`; API methods in `frontend/src/services/api.ts`
- [ ] T014 [US1] Title detail page (fields + copies list + add copy with LocationPicker) in `frontend/src/pages/TitleDetail.tsx`
- [ ] T015 [US1] Staff-only `/catalog` + `/catalog/:id` routes + nav entry (Home card + AppLayout link) in `frontend/src/App.tsx`, `Home.tsx`, `AppLayout.tsx`

**Checkpoint**: US1 functional — staff catalog titles + copies (MVP).

---

## Phase 4: User Story 2 — Maintain titles and copies (Priority: P2)

**Goal**: Edit titles; move copies; change copy status (respecting checked_out).

**Independent Test**: Edit author; move a copy; mark a copy lost; confirm + audited.

### Tests for User Story 2 ⚠️ (write first, must fail)

- [ ] T016 [P] [US2] Tests for `PATCH /titles/{id}`, `PATCH /copies/{id}` (move), `PATCH /copies/{id}/status` incl. checked_out conflict (409) and manual `checked_out` rejected (422) in `backend/tests/integration/test_catalog.py`
- [ ] T017 [P] [US2] Playwright E2E: edit title, move a copy, change a copy status in `e2e/tests/catalog.spec.ts`

### Implementation for User Story 2

- [ ] T018 [US2] Service: `update_title`, `move_copy`, `set_copy_status` (allow available/lost/withdrawn; reject manual checked_out; block conflicts), with audit, in `backend/src/services/catalog.py`
- [ ] T019 [P] [US2] Schemas: `TitleUpdate`, `CopyUpdate`, `CopyStatusUpdate` in `backend/src/schemas/catalog.py`
- [ ] T020 [US2] Router: `PATCH /titles/{id}`, `PATCH /copies/{id}`, `PATCH /copies/{id}/status` (staff + CSRF) in `backend/src/api/catalog.py`
- [ ] T021 [US2] UI: edit-title dialog; per-copy move (LocationPicker) + status controls in `frontend/src/pages/TitleDetail.tsx`; add API methods

**Checkpoint**: US1 and US2 both work.

---

## Phase 5: User Story 3 — Remove copies and titles (Priority: P3)

**Goal**: Delete copies (not while checked_out); delete titles (only when empty).

**Independent Test**: Delete available copy; blocked for checked_out; title delete blocked with copies then allowed when empty.

### Tests for User Story 3 ⚠️ (write first, must fail)

- [ ] T022 [P] [US3] Tests for `DELETE /copies/{id}` (204; 409 when checked_out) and `DELETE /titles/{id}` (409 with copies; 204 when empty) in `backend/tests/integration/test_catalog.py`
- [ ] T023 [P] [US3] Test that deleting a location holding a copy is refused in `backend/tests/integration/test_locations_items.py`
- [ ] T024 [P] [US3] Playwright E2E: delete copy allowed/blocked; delete title blocked/allowed in `e2e/tests/catalog.spec.ts`

### Implementation for User Story 3

- [ ] T025 [US3] Service: `delete_copy` (block checked_out), `delete_title` (block if has copies), with audit, in `backend/src/services/catalog.py`
- [ ] T026 [US3] Router: `DELETE /copies/{id}`, `DELETE /titles/{id}` (staff + CSRF) in `backend/src/api/catalog.py`
- [ ] T027 [US3] UI: delete copy + delete title with confirmation and clear blocked-message handling in `frontend/src/pages/TitleDetail.tsx` / `Catalog.tsx`

**Checkpoint**: All three stories independently functional.

---

## Phase 6: Polish & Cross-Cutting

- [ ] T028 [P] Verify audit entries for title/copy create/edit/move/status/delete in `backend/tests/integration/test_catalog.py`
- [ ] T029 [P] Accessibility pass: axe check on Catalog + Title detail pages and keyboard navigation in `e2e/tests/catalog.spec.ts`
- [ ] T030 Confirm ≥80% coverage for the new backend code; fill gaps
- [ ] T031 Run quickstart.md validation end-to-end (incl. location-delete-now-blocked)
- [ ] T032 [P] Security review: staff-only guards, CSRF on all mutations, barcode uniqueness under concurrency, no checked_out edits/deletes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** blocks all stories.
- **US1 (P1)** is the MVP; **US2** and **US3** build on the shared models/service.
- Recommended order: US1 → US2 → US3, then Polish.

### Within Each User Story

- Tests written and failing BEFORE implementation (Test-First).
- Models → service → schemas → router → frontend.

### Parallel Opportunities

- `[P]` tasks touch different files and can run together (schemas vs. picker vs. tests).

---

## Implementation Strategy

**MVP first**: Phase 1 → Phase 2 → Phase 3 (US1) yields a working catalog. Then add
maintenance (US2) and removal (US3), finishing with Polish. Phase 2's location
copy-count (T005) makes feature 002's location delete-guard fully live.
