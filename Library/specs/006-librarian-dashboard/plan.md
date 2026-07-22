# Implementation Plan: Librarian Dashboard

**Branch**: `006-librarian-dashboard` | **Date**: 2026-07-21 | **Spec**: [spec.md](spec.md)

## Summary

Add a staff-only `/dashboard` that aggregates existing data into an at-a-glance
snapshot: collection counts (titles, copies), circulation state (on loan,
available), overdue count, active borrowers, and pending password resets. Below
the cards, an overdue-loans panel supports a quick Return, and a recent-activity
feed shows the last 10 circulation events (from the audit log). Everything is
derived on demand — no new tables or counters. Reuses the 001–005 stack, staff
guards, circulation service, reset service, and audit log.

## Technical Context

- **Backend**: a `dashboard` service that composes counts and lists; one
  read-only endpoint `GET /api/v1/dashboard/summary` (staff). Overdue rows reuse
  `circulation.list_active(overdue_only=True)`; recent activity reads the newest
  `loan.*` audit entries.
- **Frontend**: a staff **Dashboard** page (stat cards, overdue table with Return,
  recent-activity list). Nav gets a Dashboard link; new `/dashboard` route behind
  `RequireStaff`.
- **Testing**: pytest (summary numbers, overdue return via existing endpoint,
  guard) + Playwright (stats render, overdue Return, a11y).
- No new dependencies.

## Constitution Check

- **I. Data Integrity**: PASS — read-only aggregation; the only mutation reuses the
  audited return endpoint.
- **II. Audit**: PASS — recent activity is sourced from the audit log; no new
  unaudited writes.
- **III. RBAC**: PASS — summary endpoint and route are staff-only.
- **IV. API-First**: PASS — one versioned, validated read endpoint.
- **V. Test-First**: PASS — pytest + Playwright.
- **VI. Ease of Use**: PASS — Material cards, accessible tables, clear empty states.
- **VII. Lightweight**: PASS — derived figures, no new storage, no new deps.

No violations.

## Project Structure

```text
backend/
├── src/
│   ├── services/dashboard.py   # NEW — summary aggregation + recent activity
│   └── api/dashboard.py        # NEW — GET /api/v1/dashboard/summary (staff)
└── tests/integration/test_dashboard.py  # NEW

frontend/
├── src/
│   ├── pages/Dashboard.tsx     # NEW — stat cards + overdue panel + activity
│   ├── services/api.ts         # UPDATED — dashboardSummary()
│   ├── App.tsx                 # UPDATED — /dashboard route (RequireStaff)
│   └── components/AppLayout.tsx # UPDATED — Dashboard nav link
e2e/
└── tests/dashboard.spec.ts     # NEW — stats + overdue Return + a11y
```

## Approach

- **Summary shape**: `{ titles, copies, on_loan, available, overdue, active_borrowers,
  pending_resets, overdue_loans: LoanView[], recent_activity: ActivityView[] }`.
- **Counts**: copies grouped by `CopyStatus` (available / checked_out); titles via
  count; active borrowers via distinct `borrower_id` on open loans; pending resets
  via `ResetStatus.pending` count.
- **Recent activity**: newest 10 `audit_log` rows whose action starts with `loan.`,
  mapped to `{ action, when, detail }`.
