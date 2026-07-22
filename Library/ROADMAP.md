# Library Inventory Management System — Roadmap

This roadmap lists the planned features and the intended build order. It is a
human-owned overview; each feature is fleshed out into a formal spec under
`specs/` as it is picked up via the Spec Kit `specify` step.

## Features

### Foundation
- **F1. Authentication & Account Management** — ✅ implemented (see `specs/001-auth-user-management`)
  - Sign up and login pages + backend
  - Session/token handling, logout
  - Password reset (no email): user requests reset → request queued → Admin
    verifies and issues a one-time, single-use, expiring temporary password
    (shown once) → user logs in with it and is forced to set a new password
  - Borrower self-registration; Admin/Librarian accounts created by an Administrator
  - Usernames are not email addresses
- **F2. Roles & User Management** — ✅ implemented (with F1)
  - Roles: Administrator, Librarian, Borrower
  - Bootstrap/seed the first Administrator account
  - Admin assigns/changes roles (logged)
  - View/manage user list

### Inventory Core
- **F3. Inventory Location Management** — ✅ implemented (see `specs/002-inventory-locations`)
  - Admin/Librarian define dynamic, user-configurable location schemes
    (rooms, shelves, rows, or custom)
  - Create location definitions/templates now, fill in per item later
  - Support variable depth (one level or many)
- **F4. Item / Catalog Management** — ✅ implemented (see `specs/003-item-catalog`)
  - Item model (title, ISBN, author, media type, condition, status)
  - Titles vs. individual copies
  - Add/edit/remove items (Librarian+), assign items to locations
  - Optional barcode/RFID identifiers
- **F5. Catalog Search & Browse** — ✅ implemented (see `specs/004-catalog-search`)
  - Search and browse the catalog
  - Real-time availability
  - Accessible to all roles (Borrowers included)

### Circulation
- **F6. Borrowing & Returns** — ✅ implemented (see `specs/005-borrowing-returns`)
  - Staff check out and return items on a borrower's behalf at the desk
    (no Borrower self-service); Borrowers can view their own loans
  - Loan periods, due dates
  - Overdue handling
  - Renewals (staff-initiated)

### Insight
- **F9. Librarian Dashboard** — ✅ implemented (see `specs/006-librarian-dashboard`)
  - Real-time stats: total items, on loan, available, overdue count,
    active borrowers, recent activity
  - Overdue items panel (borrower, item, due date, days overdue)
  - Password reset request queue for Admins to action

### Cross-Cutting (from the constitution)
- **F7. Audit Trail & Logging** — ✅ implemented (see `specs/007-audit-trail`)
  - Who/what/when/why for all inventory-affecting actions
  - Append-only, queryable, soft-deletes with history
- **F8. UI/UX Shell** — ✅ implemented (branded AppLayout shell + role-aware nav)
  - Material Design layout, navigation, responsive shell
  - WCAG 2.1 AA accessibility baseline
  - Role-aware navigation

## Suggested Build Order

F1 → F2 → F8 (shell) → F3 → F4 → F5 → F6 → F9 → F7 (audit woven in throughout)

## Notes / Open Scope Questions
- Overdue policy: notifications vs. fines (TBD)
- Renewals in v1 (optional)
- v1 is local-only (including the database); cloud migration is a later phase
- No email in v1 (affects password reset and notifications)
