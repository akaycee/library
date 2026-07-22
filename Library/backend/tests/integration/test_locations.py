"""Integration tests for Inventory Location Management (F3)."""

from src.core.security import hash_password
from src.models.base import Role, UserStatus
from src.models.user import User


def _make_staff(db, username="lib", role=Role.librarian, password="abcd1234"):
    u = User(
        username=username,
        username_normalized=username.casefold(),
        password_hash=hash_password(password),
        role=role,
        status=UserStatus.active,
        force_password_change=False,
    )
    db.add(u)
    db.commit()
    return u


def _login(client, username, password="abcd1234"):
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return client.cookies.get("library_csrf")


def _create(client, csrf, name, parent_id=None, type_label=None):
    return client.post(
        "/api/v1/locations",
        headers={"X-CSRF-Token": csrf},
        json={"name": name, "parent_id": parent_id, "type_label": type_label},
    )


# --- US1: build & view --------------------------------------------------------
def test_staff_builds_and_views_tree(client, db_session):
    _make_staff(db_session)
    csrf = _login(client, "lib")

    room = _create(client, csrf, "Main Room", type_label="Room")
    assert room.status_code == 201
    room_id = room.json()["id"]
    shelf = _create(client, csrf, "Shelf A", parent_id=room_id, type_label="Shelf")
    assert shelf.status_code == 201
    shelf_id = shelf.json()["id"]
    row = _create(client, csrf, "Row 1", parent_id=shelf_id)
    assert row.status_code == 201

    tree = client.get("/api/v1/locations").json()
    assert len(tree) == 1
    assert tree[0]["name"] == "Main Room"
    assert tree[0]["children"][0]["name"] == "Shelf A"
    assert tree[0]["children"][0]["children"][0]["name"] == "Row 1"


def test_sibling_name_must_be_unique_case_insensitive(client, db_session):
    _make_staff(db_session)
    csrf = _login(client, "lib")
    _create(client, csrf, "Annex")
    dup = _create(client, csrf, "annex")  # same normalized root name
    assert dup.status_code == 409
    # Same name under a different parent is allowed.
    parent = _create(client, csrf, "Wing").json()
    ok = _create(client, csrf, "Annex", parent_id=parent["id"])
    assert ok.status_code == 201


def test_borrower_cannot_access_locations(client):
    client.post("/api/v1/auth/register", json={"username": "bo", "password": "abcd1234"})
    client.post("/api/v1/auth/login", json={"username": "bo", "password": "abcd1234"})
    assert client.get("/api/v1/locations").status_code == 403


def test_admin_is_also_staff(client, db_session):
    _make_staff(db_session, username="boss", role=Role.administrator)
    csrf = _login(client, "boss")
    assert _create(client, csrf, "HQ").status_code == 201


# --- US2: rename & move -------------------------------------------------------
def test_rename_location(client, db_session):
    _make_staff(db_session)
    csrf = _login(client, "lib")
    loc = _create(client, csrf, "Old").json()
    resp = client.patch(
        f"/api/v1/locations/{loc['id']}", headers={"X-CSRF-Token": csrf}, json={"name": "New"}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


def test_move_subtree(client, db_session):
    _make_staff(db_session)
    csrf = _login(client, "lib")
    room = _create(client, csrf, "Room 1").json()
    annex = _create(client, csrf, "Annex").json()
    shelf = _create(client, csrf, "Shelf X", parent_id=room["id"]).json()
    # Move Shelf X from Room 1 to Annex
    resp = client.patch(
        f"/api/v1/locations/{shelf['id']}/move",
        headers={"X-CSRF-Token": csrf},
        json={"new_parent_id": annex["id"]},
    )
    assert resp.status_code == 200
    tree = {n["name"]: n for n in client.get("/api/v1/locations").json()}
    assert tree["Annex"]["children"][0]["name"] == "Shelf X"
    assert tree["Room 1"]["children"] == []


def test_move_into_own_descendant_is_rejected(client, db_session):
    _make_staff(db_session)
    csrf = _login(client, "lib")
    a = _create(client, csrf, "A").json()
    b = _create(client, csrf, "B", parent_id=a["id"]).json()
    # Try to move A under B (its own child) -> cycle
    resp = client.patch(
        f"/api/v1/locations/{a['id']}/move",
        headers={"X-CSRF-Token": csrf},
        json={"new_parent_id": b["id"]},
    )
    assert resp.status_code == 409


# --- US3: safe deletion -------------------------------------------------------
def test_delete_blocked_when_has_children(client, db_session):
    _make_staff(db_session)
    csrf = _login(client, "lib")
    parent = _create(client, csrf, "Parent").json()
    _create(client, csrf, "Child", parent_id=parent["id"])
    resp = client.delete(f"/api/v1/locations/{parent['id']}", headers={"X-CSRF-Token": csrf})
    assert resp.status_code == 409


def test_delete_blocked_when_has_items(client, db_session, monkeypatch):
    from src.services import locations as loc_service

    _make_staff(db_session)
    csrf = _login(client, "lib")
    loc = _create(client, csrf, "Full").json()
    monkeypatch.setattr(loc_service, "item_count", lambda db, location_id: 3)
    resp = client.delete(f"/api/v1/locations/{loc['id']}", headers={"X-CSRF-Token": csrf})
    assert resp.status_code == 409


def test_delete_empty_location_succeeds(client, db_session):
    _make_staff(db_session)
    csrf = _login(client, "lib")
    loc = _create(client, csrf, "Empty").json()
    resp = client.delete(f"/api/v1/locations/{loc['id']}", headers={"X-CSRF-Token": csrf})
    assert resp.status_code == 204
    assert client.get("/api/v1/locations").json() == []


def test_mutations_require_csrf(client, db_session):
    _make_staff(db_session)
    _login(client, "lib")
    # No CSRF header -> 403
    resp = client.post("/api/v1/locations", json={"name": "NoCsrf"})
    assert resp.status_code == 403
