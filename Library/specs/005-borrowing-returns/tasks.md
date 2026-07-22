---
description: "Task list for Borrowing & Returns"
---

# Tasks: Borrowing & Returns

**Input**: Design documents from `specs/005-borrowing-returns/`
**Tests**: Included and REQUIRED (Test-First).

## Phase 1: Foundational

- [ ] T001 Create the `Loan` model (copy_id, borrower_id, checked_out_by, borrowed_at, due_at, returned_at, renewal_count) in `backend/src/models/loan.py`; register in `backend/src/models/__init__.py`

## Phase 2: US1+US2 — Checkout & Return (P1, MVP)

- [ ] T002 [P] Tests: checkout by barcode+username sets checked_out + due date; refuses unavailable copy / unknown borrower / bad period; return restores available; borrower cannot check out in `backend/tests/integration/test_circulation.py`
- [ ] T003 Circulation service: `checkout`, `return_loan` (with guards + audit) in `backend/src/services/circulation.py`
- [ ] T004 Loans router: `POST /loans` (checkout), `POST /loans/{id}/return`, `GET /loans` (active, staff) in `backend/src/api/loans.py`; wire into `backend/src/main.py`
- [ ] T005 [P] Playwright E2E: staff checks out a copy then returns it in `e2e/tests/circulation.spec.ts`
- [ ] T006 Staff Circulation page (checkout form + active loans with return) in `frontend/src/pages/Circulation.tsx`; loan API methods in `frontend/src/services/api.ts`
- [ ] T007 Staff `/circulation` route + nav entry (AppLayout + Home card) in `frontend/src/App.tsx`, `Home.tsx`, `AppLayout.tsx`

## Phase 3: US3 — Renew & Overdue (P2)

- [ ] T008 [P] Tests: renew extends due date + increments count; overdue renewal refused; overdue loans flagged in `backend/tests/integration/test_circulation.py`
- [ ] T009 Service: `renew` (block if overdue) + overdue derivation in active-loan list in `backend/src/services/circulation.py`
- [ ] T010 Router: `POST /loans/{id}/renew`; include `overdue` flag + `GET /loans?status=overdue` in `backend/src/api/loans.py`
- [ ] T011 UI: renew action + overdue highlight on the Circulation page in `frontend/src/pages/Circulation.tsx`
- [ ] T012 [P] Playwright E2E: renew a loan; overdue flagged in `e2e/tests/circulation.spec.ts`

## Phase 4: US4 — Borrower "My loans" (P3)

- [ ] T013 [P] Tests: `GET /loans/mine` returns only the caller's active loans in `backend/tests/integration/test_circulation.py`
- [ ] T014 Router: `GET /loans/mine` (any authenticated) in `backend/src/api/loans.py`
- [ ] T015 Borrower My Loans page + `/my-loans` route + nav/Home card in `frontend/src/pages/MyLoans.tsx`, `App.tsx`, `AppLayout.tsx`, `Home.tsx`

## Phase 5: Polish

- [ ] T016 [P] Verify audit entries for checkout/return/renew in `backend/tests/integration/test_circulation.py`
- [ ] T017 [P] Accessibility: axe check on Circulation + My Loans pages in `e2e/tests/circulation.spec.ts`
- [ ] T018 Confirm ≥80% coverage for new code; run quickstart validation

## Dependencies
- Phase 1 → US1/US2 (P1) → US3 (P2) → US4 (P3) → Polish. Test-First within each.
