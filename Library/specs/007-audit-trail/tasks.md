# Tasks: Audit Trail & Logging (F7)

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Backend

- [x] T001 `services/audit_query.py` — `list_entries(db, *, action, q, start, end,
      limit, offset)` newest-first, resolving actor/target usernames (single map).
- [x] T002 `services/audit_query.py` — `action_types(db)` distinct actions sorted.
- [x] T003 `api/audit.py` — `GET /api/v1/audit` (staff, filters + paging) and
      `GET /api/v1/audit/actions` (staff); wire in `main.py`.
- [x] T004 `tests/integration/test_audit.py` — ordering, action filter, username
      filter, date range, paging, borrower forbidden.

## Frontend

- [x] T005 `services/api.ts` — `AuditEntry` type + `listAudit()` / `auditActions()`.
- [x] T006 `pages/Audit.tsx` — action dropdown, username search, date range, table.
- [x] T007 `App.tsx` — `/audit` route behind `RequireStaff`.
- [x] T008 `components/AppLayout.tsx` — Audit nav link (staff).

## Verification

- [x] T009 `e2e/tests/audit.spec.ts` — list renders, filter narrows, a11y.
- [x] T010 Also add an E2E covering borrower quick-create at the desk.
- [x] T011 Run pytest, frontend build, full Playwright; mark spec Implemented +
      tick ROADMAP F7.
