---
description: "Task list for Catalog Search & Browse"
---

# Tasks: Catalog Search & Browse

**Input**: Design documents from `specs/004-catalog-search/`
**Tests**: Included and REQUIRED (Test-First).

## Phase 1: Foundational

- [ ] T001 Browse service: `search_titles(db, q)` returning each title with `available_count`/`total_count` via SQL aggregation over Copy.status in `backend/src/services/browse.py`

## Phase 2: User Story 1 — Browse (P1, MVP)

- [ ] T002 [P] [US1] Tests: any authenticated role can browse; availability counts match; unauthenticated → 401 in `backend/tests/integration/test_browse.py`
- [ ] T003 [US1] Schema `BrowseItem` + `GET /api/v1/browse` (auth any role; no barcodes/locations) in `backend/src/api/browse.py`; wire into `backend/src/main.py`
- [ ] T004 [P] [US1] Playwright E2E: a borrower opens Browse and sees titles with availability in `e2e/tests/browse.spec.ts`
- [ ] T005 [US1] Browse page (list with availability) in `frontend/src/pages/Browse.tsx`; `browse` API method in `frontend/src/services/api.ts`
- [ ] T006 [US1] Add a `/browse` route + nav entry for all roles (AppLayout + Home card) in `frontend/src/App.tsx`, `Home.tsx`, `AppLayout.tsx`

## Phase 3: User Story 2 — Search (P2)

- [ ] T007 [P] [US2] Tests: substring match on name/author/isbn (case-insensitive); empty query returns all; no match returns empty in `backend/tests/integration/test_browse.py`
- [ ] T008 [US2] Add `q` query param to `GET /api/v1/browse` (service already supports it)
- [ ] T009 [US2] Search box on the Browse page (debounced or on submit) with empty-state message in `frontend/src/pages/Browse.tsx`
- [ ] T010 [P] [US2] Playwright E2E: search narrows results; no-match empty state in `e2e/tests/browse.spec.ts`

## Phase 4: Polish

- [ ] T011 [P] Verify borrower response contains no barcodes/locations (privacy) in `backend/tests/integration/test_browse.py`
- [ ] T012 [P] Accessibility: axe check on the Browse page in `e2e/tests/browse.spec.ts`
- [ ] T013 Confirm ≥80% coverage for new code; run quickstart validation

## Dependencies

- Phase 1 → Phase 2 (US1) → Phase 3 (US2) → Polish.
- Tests before implementation within each story (Test-First).
