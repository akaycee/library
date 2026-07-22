# Implementation Plan: Item / Catalog Management

**Branch**: `003-item-catalog` | **Date**: 2026-07-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-item-catalog/spec.md`

## Summary

Add a staff-managed **catalog** of bibliographic **Titles**, each with one or more
physical **Copies**. A copy has a unique auto-generated barcode, lives at a
**Location** (from feature 002), and carries a status (`available`, `checked_out`,
`lost`, `withdrawn`). This feature also implements the **real location copy-count**,
replacing the temporary `item_count` hook from the locations feature so that
"cannot delete a location that holds copies" becomes live.

Reuses the feature 001/002 stack (FastAPI + SQLAlchemy + SQLite/SQLCipher; React +
Vite + MUI) plus its auth, roles, staff guards, locations, and audit infrastructure.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x / React 18 (frontend)

**Primary Dependencies**: existing only — FastAPI, SQLAlchemy 2.x, Pydantic v2, MUI. No new dependencies.

**Storage**: New `titles` and `copies` tables via SQLAlchemy; created by `create_all`.

**Testing**: pytest + httpx (backend), Playwright + axe (E2E).

**Target Platform**: Same single-process local deployment.

**Project Type**: Web application (extends existing backend + frontend).

**Performance Goals**: Catalog list well under the 500ms budget for hundreds of titles/copies.

**Constraints**: Staff-only; all mutations audited + CSRF-protected; unique barcodes; respect `checked_out` (owned by the future borrowing feature).

**Scale/Scope**: Hundreds of titles and copies; a handful of concurrent staff.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Data Integrity First**: PASS — all mutations transactional; barcode uniqueness enforced; delete/status guards prevent removing checked-out copies or non-empty titles; the accurate copy-count prevents orphaning copies when locations are deleted.
- **II. Complete Audit Trail**: PASS — title/copy create/edit/move/status/delete each write an append-only audit entry with who/what/when/why.
- **III. Role-Based Access Control**: PASS — reuses `require_staff`/`require_staff_write` (Administrator or Librarian); Borrowers denied.
- **IV. API-First Design**: PASS — versioned `/api/v1` catalog endpoints with Pydantic validation before the UI consumes them.
- **V. Test-First**: PASS — pytest covers barcode uniqueness, status/delete guards, and the location count; Playwright covers the staff catalog UI.
- **VI. Ease of Use**: PASS — a clear MUI catalog (titles list → title detail with copies), a location picker reused from feature 002, forgiving errors.
- **VII. Lightweight & Low-Maintenance**: PASS — two simple tables, sequential-accession barcode scheme, no new dependencies or services.

No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/003-item-catalog/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── catalog-api.md
├── checklists/
│   └── requirements.md
└── tasks.md            # Created later by /speckit.tasks
```

### Source Code (extends the existing app)

```text
backend/
├── src/
│   ├── models/title.py          # NEW — Title
│   ├── models/copy.py           # NEW — Copy (barcode, location_id, status)
│   ├── models/base.py           # UPDATED — add CopyStatus enum
│   ├── schemas/catalog.py       # NEW — title/copy create/update/view
│   ├── services/catalog.py      # NEW — titles/copies CRUD, barcode gen, guards, audit
│   ├── services/locations.py    # UPDATED — item_count now counts copies
│   └── api/catalog.py           # NEW — /api/v1/titles + copies router
└── tests/integration/test_catalog.py           # NEW
    tests/integration/test_locations_items.py    # NEW — location delete blocked by copies

frontend/
├── src/
│   ├── pages/Catalog.tsx        # NEW — titles list + add title
│   ├── pages/TitleDetail.tsx    # NEW — title fields + copies (add/move/status/delete)
│   ├── components/LocationPicker.tsx  # NEW — reuse tree flattening for a location select
│   └── services/api.ts          # UPDATED — catalog methods
└── (App.tsx, Home.tsx, AppLayout.tsx UPDATED — staff Catalog route + nav)

e2e/
└── tests/catalog.spec.ts        # NEW — add title + copies, move, status, delete guards
```

**Structure Decision**: Extend the existing web app with a catalog vertical slice
(models → service → router → UI) mirroring features 001–002 for consistency.

## Complexity Tracking

No constitution violations — section intentionally empty.
