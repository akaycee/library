# API Contract: Inventory Location Management

**Feature**: Inventory Location Management
**Base path**: `/api/v1/locations`
**Format**: JSON, schema-validated.
**Auth**: Session cookie; **staff only** (Administrator or Librarian). Mutations
require the CSRF token (double-submit) as in feature 001. Borrowers → 403.

## GET /api/v1/locations
Return the full location tree (roots with nested children).
- **200**: `[ LocationNode ]` where
  ```
  LocationNode = {
    "id": string,
    "name": string,
    "type_label": string | null,
    "parent_id": string | null,
    "children": [ LocationNode ]
  }
  ```
- **403**: non-staff
- Maps to: FR-005, FR-013

## POST /api/v1/locations
Create a location (root if `parent_id` is null).
- **Body**: `{ "name": string, "type_label"?: string | null, "parent_id"?: string | null }`
- **201**: the created node (without children)
- **403**: non-staff
- **404**: `parent_id` does not exist
- **409**: a sibling with the same name already exists
- **422**: empty/invalid name
- Maps to: FR-001, FR-002, FR-003, FR-004, FR-014

## PATCH /api/v1/locations/{id}
Rename and/or set the type label.
- **Body**: `{ "name"?: string, "type_label"?: string | null }`
- **200**: updated node
- **403**: non-staff
- **404**: not found
- **409**: rename would duplicate a sibling name
- **422**: empty/invalid name
- Maps to: FR-006, FR-009, FR-014

## PATCH /api/v1/locations/{id}/move
Reparent a location (and its subtree). `new_parent_id` null moves it to root.
- **Body**: `{ "new_parent_id": string | null }`
- **200**: updated node
- **403**: non-staff
- **404**: location or new parent not found
- **409**: would create a cycle, or would duplicate a sibling name at the destination
- Maps to: FR-007, FR-008, FR-009, FR-014

## DELETE /api/v1/locations/{id}
Delete an empty location.
- **204**: deleted
- **403**: non-staff
- **404**: not found
- **409**: location has child locations or items (not empty)
- Maps to: FR-010, FR-011, FR-012, FR-014

## Authorization Matrix

| Endpoint            | Borrower | Librarian | Administrator |
|---------------------|:--------:|:---------:|:-------------:|
| GET  /locations     | ❌       | ✅        | ✅            |
| POST /locations     | ❌       | ✅        | ✅            |
| PATCH /locations/*  | ❌       | ✅        | ✅            |
| DELETE /locations/* | ❌       | ✅        | ✅            |

Maps to: FR-013

## Cross-cutting

- Every create/rename/move/delete writes an append-only `AuditLogEntry` (FR-014).
- All mutations require a valid CSRF token and are transactional.
- Errors return a clear, user-facing `detail` message.
