# Implementation Plan: Borrowing & Returns

**Branch**: `005-borrowing-returns` | **Date**: 2026-07-20 | **Spec**: [spec.md](spec.md)

## Summary

Add circulation: a staff-only desk model to check out copies (by barcode) to
borrowers (by username) with a per-checkout loan period, return them, and renew
active non-overdue loans; overdue loans are flagged. Borrowers get a read-only
"My loans" view. A new `Loan` entity ties a Copy to a borrower; checkout sets the
copy `checked_out` (already respected by the catalog/browse features) and return
restores `available`. Reuses features 001–004 stack, auth, staff guards, and audit.

## Technical Context

- **Backend**: `Loan` model; circulation service (checkout/return/renew, overdue
  derivation, lists); `/api/v1/loans` endpoints — staff for mutations + active/overdue
  lists, and `/loans/mine` for any authenticated user.
- **Frontend**: staff **Circulation** page (checkout form + active loans with
  return/renew, overdue highlighted) and a borrower **My loans** page. Nav updated.
- **Testing**: pytest (checkout/return/renew/overdue/guards/availability) + Playwright.
- No new dependencies.

## Constitution Check

- **I. Data Integrity**: PASS — transactional; a copy can't be double-loaned (checkout requires `available` then flips to `checked_out`); return/renew guarded.
- **II. Audit**: PASS — checkout/return/renew audited with who/what/when/why.
- **III. RBAC**: PASS — circulation mutations staff-only; borrowers only read their own loans.
- **IV. API-First**: PASS — versioned endpoints with validated models.
- **V. Test-First**: PASS — pytest + Playwright.
- **VI. Ease of Use**: PASS — desk-friendly barcode+username checkout; clear overdue flags; accessible.
- **VII. Lightweight**: PASS — one table, derived overdue, no new deps.

No violations.

## Project Structure

```text
backend/
├── src/
│   ├── models/loan.py         # NEW — Loan
│   ├── services/circulation.py # NEW — checkout/return/renew/lists/overdue
│   └── api/loans.py           # NEW — /api/v1/loans (staff + /mine)
└── tests/integration/test_circulation.py  # NEW

frontend/
├── src/
│   ├── pages/Circulation.tsx  # NEW — staff checkout + active loans
│   ├── pages/MyLoans.tsx      # NEW — borrower read-only loans
│   └── services/api.ts        # UPDATED — loan methods
└── (App.tsx, Home.tsx, AppLayout.tsx UPDATED — routes + nav)

e2e/
└── tests/circulation.spec.ts  # NEW — checkout → return → renew/overdue
```

**Structure Decision**: Circulation vertical slice reusing catalog + users.

## Complexity Tracking

No violations — intentionally empty.
