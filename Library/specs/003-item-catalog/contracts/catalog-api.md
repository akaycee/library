# API Contract: Item / Catalog Management

**Feature**: Item / Catalog Management
**Base path**: `/api/v1`
**Format**: JSON, schema-validated.
**Auth**: Session cookie; **staff only** (Administrator or Librarian). Mutations
require the CSRF token (double-submit). Borrowers → 403.

## Titles

### GET /api/v1/titles
List titles (with copy counts).
- **200**: `[ { "id", "name", "author", "isbn", "media_type", "copy_count" } ]`
- **403**: non-staff
- Maps to: FR-002, FR-012

### POST /api/v1/titles
Create a title.
- **Body**: `{ "name": string, "author"?: string, "isbn"?: string, "media_type"?: string }`
- **201**: the created title
- **403**: non-staff
- **422**: empty/invalid name
- Maps to: FR-001, FR-013

### GET /api/v1/titles/{id}
Title detail with its copies.
- **200**: `{ "id", "name", "author", "isbn", "media_type", "copies": [ CopyView ] }`
  where `CopyView = { "id", "barcode", "location_id", "location_path", "status", "condition" }`
- **404**: not found
- Maps to: FR-002

### PATCH /api/v1/titles/{id}
Edit a title.
- **Body**: `{ "name"?, "author"?, "isbn"?, "media_type"? }`
- **200**: updated title
- **404**: not found
- **422**: invalid name
- Maps to: FR-003, FR-013

### DELETE /api/v1/titles/{id}
Delete a title (only if it has no copies).
- **204**: deleted
- **404**: not found
- **409**: title still has copies
- Maps to: FR-004, FR-013

## Copies

### POST /api/v1/titles/{id}/copies
Add a copy to a title.
- **Body**: `{ "location_id": string, "barcode"?: string, "condition"?: string }`
- **201**: created copy (barcode auto-assigned if omitted)
- **404**: title or location not found
- **409**: manual barcode already exists
- **422**: missing location
- Maps to: FR-005, FR-006, FR-013

### PATCH /api/v1/copies/{id}
Move a copy and/or set condition.
- **Body**: `{ "location_id"?: string, "condition"?: string }`
- **200**: updated copy
- **404**: copy or location not found
- Maps to: FR-007, FR-013

### PATCH /api/v1/copies/{id}/status
Change a copy's status (manual: available/lost/withdrawn).
- **Body**: `{ "status": "available" | "lost" | "withdrawn" }`
- **200**: updated copy
- **404**: not found
- **409**: copy is `checked_out` (resolve the loan first) or invalid transition
- **422**: `checked_out` cannot be set manually
- Maps to: FR-008, FR-009, FR-013

### DELETE /api/v1/copies/{id}
Delete a copy (not while `checked_out`).
- **204**: deleted
- **404**: not found
- **409**: copy is `checked_out`
- Maps to: FR-009, FR-010, FR-013

## Authorization Matrix

| Endpoint group      | Borrower | Librarian | Administrator |
|---------------------|:--------:|:---------:|:-------------:|
| titles/* , copies/* | ❌       | ✅        | ✅            |

Maps to: FR-012

## Cross-cutting

- Every mutation writes an append-only `AuditLogEntry` (FR-013) and requires CSRF.
- Barcode uniqueness enforced by a DB constraint plus a friendly service check.
- The location copy-count powers the locations delete-guard (feature 002 FR-011).
