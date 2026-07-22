# Quickstart: Item / Catalog Management

**Feature**: Item / Catalog Management
**Audience**: Developers running the app locally.

Extends the existing app — no new services or dependencies. Requires the locations
feature (002) for placing copies.

## Run (single-process, dev)

```powershell
cd "C:\Users\anirudhk\Desktop\library\Library\frontend"
npm run build

cd ..\backend
$env:LIBRARY_COOKIE_SECURE = "false"
.\.venv\Scripts\python.exe -m src.core.schema_init   # creates titles + copies tables
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

## Try it (as staff)

1. Sign in as an Administrator or Librarian.
2. Create at least one location (Locations page) so copies have somewhere to live.
3. Open **Catalog** → add a title (e.g., "Charlotte's Web", author "E.B. White").
4. Open the title → add two copies, choosing locations; note the auto barcodes.
5. Move a copy to another location; mark one copy `lost`; delete an available copy.
6. Try deleting a title that still has copies → refused; remove copies → delete → succeeds.
7. Try deleting a location that holds a copy (Locations page) → now refused.

## Tests

```powershell
# Backend
cd backend
.\.venv\Scripts\python.exe -m pytest tests/integration/test_catalog.py tests/integration/test_locations_items.py -q

# End-to-end
cd ..\e2e
npx playwright test catalog
```

## Notes

- `checked_out` is set by the future borrowing feature; here it only blocks
  conflicting edits/deletes.
- Barcodes are auto-assigned (e.g., `LIB-000001`) unless you enter a unique one.
