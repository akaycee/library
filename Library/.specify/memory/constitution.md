# Library Inventory Management System Constitution

## Core Principles

### I. Data Integrity First (NON-NEGOTIABLE)
Inventory records are the single source of truth and must always be accurate.
- Every mutation (add, remove, check-out, return, transfer) MUST execute inside a database transaction.
- No operation may leave counts, statuses, or holdings in a partial or ambiguous state.
- Reconciliation checks MUST be possible at any time; the system prefers rejecting an operation over recording an inconsistent one.

### II. Complete Audit Trail
Nothing changes silently.
- Every inventory-affecting action MUST record who, what, when, and why.
- Records are append-only; deletions are logical (soft-delete) with retained history.
- Audit logs MUST be queryable and MUST NOT be editable through normal application flows.

### III. Role-Based Access Control
Access is least-privilege by default.
- Distinct roles MUST be enforced: Administrator, Librarian, and Borrower.
- Administrators have full access to all system functions, including user and role management.
- Librarians have full access to inventory and library operations but not system administration.
- Borrowers have read-only access to the catalog and their own account, including their current and past loans; circulation (checkout, return, renewal) is performed on their behalf by staff at the desk — Borrowers do NOT self-serve. All write operations require Librarian or above.
- Privilege changes MUST be logged and require an Administrator.

### IV. API-First Design
All functionality is exposed through a documented, versioned API.
- Every feature MUST be reachable via the API before any UI is built on top of it.
- Requests and responses MUST use validated JSON schemas; invalid payloads are rejected at the boundary.
- Breaking API changes require a new version; old versions remain supported through a documented deprecation window.

### V. Test-First (NON-NEGOTIABLE)
Correctness is proven, not assumed.
- Tests MUST be written and reviewed before implementation; Red-Green-Refactor is enforced.
- Minimum 80% unit test coverage; core workflows (search → reserve → checkout → return) MUST have integration tests.
- No feature merges without passing tests and at least one domain-informed review.

### VI. Ease of Use (NON-NEGOTIABLE)
The interface serves librarians of varying technical comfort and must be usable without training.
- The UI MUST be intuitive and minimal, prioritizing clarity over feature density.
- Layouts, typography, and interactions MUST follow Material Design principles for consistency and accessibility.
- Common tasks (search, checkout, return) MUST be reachable in the fewest reasonable steps, with clear labels and forgiving error handling.
- The interface MUST meet WCAG 2.1 AA accessibility standards, including sufficient contrast, keyboard navigation, and readable font sizes.

### VII. Lightweight & Low-Maintenance (NON-NEGOTIABLE)
The system runs in a small, resource-constrained library staffed by non-technical people; every decision favors the simplest thing that works.
- Solutions MUST prefer the most lightweight, low-cost option that satisfies the requirement; complexity and dependencies MUST be justified, not assumed.
- New dependencies, services, and infrastructure MUST be avoided unless a simpler in-scope alternative cannot meet the need.
- Operational overhead MUST be minimized: prefer zero-config, self-contained, and offline-capable choices for the local deployment.
- Features MUST NOT be over-engineered; build only what the current requirement needs (YAGNI).

## Additional Constraints

- **Deployment**: Version 1 runs entirely locally, including its database; the architecture MUST avoid hard dependencies on any specific cloud provider so the system and its data can later be migrated to the cloud without rework.
- **Real-time availability**: Borrower-facing availability queries MUST reflect current state with no stale reads for checkout-critical paths.
- **Performance**: Standard catalog queries under 500ms; bulk import under 5 seconds per 100 items.
- **Security & Privacy**: Borrower PII MUST be encrypted at rest and in transit; access to PII is logged.
- **Compliance**: Data retention and disposal MUST follow applicable jurisdictional requirements.
- **Interoperability**: The system SHOULD support barcode/RFID scanning workflows for physical items.

## Development Workflow

- All changes go through pull request with at least one reviewer; changes touching inventory logic require a domain-expert (librarian) reviewer.
- CI MUST run the full test suite and schema validation on every PR; failing checks block merge.
- Database migrations MUST be reversible and reviewed separately from feature logic.
- Feature work follows the Spec-Driven flow: specify → plan → tasks → implement, with review gates between phases.

## Governance

- This constitution supersedes all other practices; when guidance conflicts, the constitution wins.
- Amendments MUST be documented, justified, and approved by an Administrator, with a migration plan when they affect existing behavior.
- All PRs and reviews MUST verify compliance with these principles; unavoidable complexity MUST be explicitly justified.

**Version**: 2.2.0 | **Ratified**: 2026-07-18 | **Last Amended**: 2026-07-21
