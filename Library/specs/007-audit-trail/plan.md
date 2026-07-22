# Implementation Plan: Audit Trail & Logging

**Branch**: `007-audit-trail` | **Date**: 2026-07-21 | **Spec**: [spec.md](spec.md)

## Summary

Add a staff-facing viewer over the existing append-only `audit_log`. A read
service lists entries newest-first with actor/target usernames resolved and
supports filters (action type, username contains, from/to date) plus limit/offset
paging; a companion call returns the distinct action types for the filter control.
A new `/audit` page renders the filters and a results table. No writes are added —
every feature already records to the shared log (constitution II).

## Technical Context

- **Backend**: `services/audit_query.py` — `list_entries(...)` and `action_types()`;
  `api/audit.py` — `GET /api/v1/audit` and `GET /api/v1/audit/actions` (staff).
  Usernames resolved via a single id→username map to avoid N+1.
- **Frontend**: **Audit** page (action dropdown, username search, date range, table)
  behind `RequireStaff`; nav link; `api.ts` methods + types.
- **Testing**: pytest (ordering, each filter, guard, paging) + Playwright
  (list renders, filter narrows, a11y).
- No new dependencies; no schema changes.

## Constitution Check

- **I. Data Integrity**: PASS — read-only; no mutations.
- **II. Audit**: PASS — this *is* the audit surface; log stays append-only.
- **III. RBAC**: PASS — staff-only route + endpoints.
- **IV. API-First**: PASS — versioned, validated read endpoints.
- **V. Test-First**: PASS — pytest + Playwright.
- **VI. Ease of Use**: PASS — accessible filters + table, clear empty states.
- **VII. Lightweight**: PASS — paginated queries, no new storage or deps.

No violations.

## Project Structure

```text
backend/
├── src/
│   ├── services/audit_query.py  # NEW — list_entries + action_types (read)
│   └── api/audit.py             # NEW — GET /audit, GET /audit/actions (staff)
└── tests/integration/test_audit.py  # NEW

frontend/
├── src/
│   ├── pages/Audit.tsx          # NEW — filters + results table
│   ├── services/api.ts          # UPDATED — audit types + methods
│   ├── App.tsx                  # UPDATED — /audit route (RequireStaff)
│   └── components/AppLayout.tsx # UPDATED — Audit nav link
e2e/
└── tests/audit.spec.ts          # NEW — list + filter + a11y
```

## Approach

- **Entry shape**: `{ id, action, actor, target, reason, created_at }` where
  `actor`/`target` are usernames (or `null`/"system" for no actor).
- **Filters**: `action` exact; `q` case-insensitive contains against actor OR target
  username (resolve candidate user ids first, then filter on id sets); `start`/`end`
  ISO dates on `created_at`.
- **Paging**: `limit` (default 50, cap 200) + `offset`; return newest-first.
- **Action types**: `SELECT DISTINCT action ORDER BY action`.
