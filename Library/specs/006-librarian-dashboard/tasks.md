# Tasks: Librarian Dashboard (F9)

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Backend

- [x] T001 `services/dashboard.py` — `summary(db)` composing counts (titles, copies,
      on_loan, available, overdue, active_borrowers, pending_resets).
- [x] T002 `services/dashboard.py` — `recent_activity(db, limit=10)` from the audit
      log (`loan.*` actions), newest-first.
- [x] T003 `api/dashboard.py` — `GET /api/v1/dashboard/summary` (staff) returning
      stats + overdue loans + recent activity; wire in `main.py`.
- [x] T004 `tests/integration/test_dashboard.py` — stats correctness, overdue row +
      return, borrower is forbidden.

## Frontend

- [x] T005 `services/api.ts` — `DashboardSummary` types + `dashboardSummary()`.
- [x] T006 `pages/Dashboard.tsx` — stat cards, overdue table with Return, recent
      activity list.
- [x] T007 `App.tsx` — `/dashboard` route behind `RequireStaff`.
- [x] T008 `components/AppLayout.tsx` — Dashboard nav link (staff).

## Verification

- [x] T009 `e2e/tests/dashboard.spec.ts` — stats render, overdue Return, a11y.
- [x] T010 Run pytest, frontend build, and full Playwright suite; mark spec
      Implemented + tick ROADMAP F9.
