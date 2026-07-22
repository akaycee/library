# Implementation Plan: Catalog Search & Browse

**Branch**: `004-catalog-search` | **Date**: 2026-07-20 | **Spec**: [spec.md](spec.md)

## Summary

Add a read-only, borrower-facing **Browse & Search** view over the existing
catalog: any signed-in user can list/search titles (by name/author/ISBN) and see
per-title **availability** (available copies over total), computed live. No new
persistent entities — a new aggregate endpoint + a Browse page. Reuses the
features 001–003 stack, auth, and roles.

## Technical Context

- **Backend**: new `GET /api/v1/browse` (auth required, any role) returning
  `{ id, name, author, media_type, available_count, total_count }[]`, with an
  optional `q` substring filter across name/author/isbn. Availability derived from
  copy status via SQL aggregation.
- **Frontend**: a Browse page (search box + results) reachable by all roles; the
  borrower's Home "Catalog" card becomes real.
- **Testing**: pytest (search/availability/privacy) + Playwright (borrower browse/search).
- No new dependencies.

## Constitution Check

- **I. Data Integrity**: PASS — read-only; availability computed from source of truth.
- **II. Audit**: N/A — read-only browsing is not a mutation (no audit needed).
- **III. RBAC**: PASS — requires authentication (`get_current`); any role may read; no mutations exposed. Borrower view omits barcodes/locations.
- **IV. API-First**: PASS — versioned endpoint with a validated response model.
- **V. Test-First**: PASS — pytest + Playwright.
- **VI. Ease of Use**: PASS — simple search box + clear availability labels; accessible.
- **VII. Lightweight**: PASS — one aggregate query, no new tables/deps.

No violations.

## Project Structure

```text
backend/
├── src/
│   ├── services/browse.py     # NEW — search + availability aggregation
│   └── api/browse.py          # NEW — GET /api/v1/browse (any authenticated role)
└── tests/integration/test_browse.py   # NEW

frontend/
├── src/
│   ├── pages/Browse.tsx       # NEW — search box + results with availability
│   └── services/api.ts        # UPDATED — browse method
└── (App.tsx, Home.tsx, AppLayout.tsx UPDATED — Browse route + nav for all roles)

e2e/
└── tests/browse.spec.ts       # NEW — borrower browses/searches
```

**Structure Decision**: Small read-only vertical slice reusing catalog data.

## Complexity Tracking

No violations — intentionally empty.
