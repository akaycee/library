# Quickstart: Inventory Location Management

**Feature**: Inventory Location Management
**Audience**: Developers running the app locally.

This feature extends the existing app — no new services or dependencies. If you
have feature 001 running, you already have everything needed.

## Run (single-process, dev)

```powershell
cd "C:\Users\anirudhk\Desktop\library\Library\frontend"
npm run build

cd ..\backend
$env:LIBRARY_COOKIE_SECURE = "false"
.\.venv\Scripts\python.exe -m src.core.schema_init   # creates the new locations table too
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

The `locations` table is created automatically on startup (`create_all`).

## Try it (as staff)

1. Sign in as an Administrator or Librarian.
2. Open **Locations** from the nav.
3. Create a root location (e.g., "Main Room", type label "Room").
4. Add a child under it ("Shelf A", type "Shelf"), then a grandchild ("Row 1").
5. Rename a location; move "Shelf A" under a different room.
6. Try to delete a non-empty location → refused; delete an empty one → succeeds.

## Tests

```powershell
# Backend
cd backend
.\.venv\Scripts\python.exe -m pytest tests/integration/test_locations.py -q

# End-to-end
cd ..\e2e
npx playwright test locations
```

## Notes

- Borrowers cannot see or reach the Locations page or API (staff-only).
- The item check for deletion returns 0 until the catalog feature exists, so for
  now deletion is blocked only by child locations.
