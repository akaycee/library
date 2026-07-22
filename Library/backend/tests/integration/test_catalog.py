"""Integration tests for Item / Catalog Management (F4)."""

from sqlalchemy import select

from src.core.security import hash_password
from src.models.base import CopyStatus, Role, UserStatus
from src.models.copy import Copy
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


def _login(client, username="lib", password="abcd1234"):
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return client.cookies.get("library_csrf")


def _h(csrf):
    return {"X-CSRF-Token": csrf}


def _make_location(client, csrf, name="Room"):
    return client.post("/api/v1/locations", headers=_h(csrf), json={"name": name}).json()


def _make_title(client, csrf, name="Charlotte's Web", author="E.B. White"):
    return client.post(
        "/api/v1/titles", headers=_h(csrf), json={"name": name, "author": author}
    ).json()


# --- US1 ----------------------------------------------------------------------
def test_add_title_and_copies_with_auto_barcodes(client, db_session):
    _make_staff(db_session)
    csrf = _login(client)
    loc = _make_location(client, csrf)
    title = _make_title(client, csrf)

    c1 = client.post(f"/api/v1/titles/{title['id']}/copies", headers=_h(csrf), json={"location_id": loc["id"]})
    c2 = client.post(f"/api/v1/titles/{title['id']}/copies", headers=_h(csrf), json={"location_id": loc["id"]})
    assert c1.status_code == 201 and c2.status_code == 201
    assert c1.json()["barcode"] != c2.json()["barcode"]
    assert c1.json()["status"] == "available"

    detail = client.get(f"/api/v1/titles/{title['id']}").json()
    assert len(detail["copies"]) == 2
    assert detail["copies"][0]["location_path"] == "Room"


def test_manual_barcode_must_be_unique(client, db_session):
    _make_staff(db_session)
    csrf = _login(client)
    loc = _make_location(client, csrf)
    title = _make_title(client, csrf)
    client.post(f"/api/v1/titles/{title['id']}/copies", headers=_h(csrf), json={"location_id": loc["id"], "barcode": "X-1"})
    dup = client.post(f"/api/v1/titles/{title['id']}/copies", headers=_h(csrf), json={"location_id": loc["id"], "barcode": "X-1"})
    assert dup.status_code == 409


def test_copy_requires_location(client, db_session):
    _make_staff(db_session)
    csrf = _login(client)
    title = _make_title(client, csrf)
    resp = client.post(f"/api/v1/titles/{title['id']}/copies", headers=_h(csrf), json={})
    assert resp.status_code == 422


def test_borrower_cannot_access_catalog(client):
    client.post("/api/v1/auth/register", json={"username": "bo", "password": "abcd1234"})
    client.post("/api/v1/auth/login", json={"username": "bo", "password": "abcd1234"})
    assert client.get("/api/v1/titles").status_code == 403


# --- US2 ----------------------------------------------------------------------
def test_edit_title_and_move_copy(client, db_session):
    _make_staff(db_session)
    csrf = _login(client)
    loc1 = _make_location(client, csrf, "Room 1")
    loc2 = _make_location(client, csrf, "Room 2")
    title = _make_title(client, csrf)
    copy = client.post(f"/api/v1/titles/{title['id']}/copies", headers=_h(csrf), json={"location_id": loc1["id"]}).json()

    upd = client.patch(f"/api/v1/titles/{title['id']}", headers=_h(csrf), json={"author": "New Author"})
    assert upd.status_code == 200 and upd.json()["author"] == "New Author"

    moved = client.patch(f"/api/v1/copies/{copy['id']}", headers=_h(csrf), json={"location_id": loc2["id"]})
    assert moved.status_code == 200 and moved.json()["location_path"] == "Room 2"


def test_status_change_rules(client, db_session):
    _make_staff(db_session)
    csrf = _login(client)
    loc = _make_location(client, csrf)
    title = _make_title(client, csrf)
    copy = client.post(f"/api/v1/titles/{title['id']}/copies", headers=_h(csrf), json={"location_id": loc["id"]}).json()

    # available -> lost is fine
    assert client.patch(f"/api/v1/copies/{copy['id']}/status", headers=_h(csrf), json={"status": "lost"}).status_code == 200
    # cannot set checked_out manually
    assert client.patch(f"/api/v1/copies/{copy['id']}/status", headers=_h(csrf), json={"status": "checked_out"}).status_code == 422


def test_checked_out_copy_blocks_status_and_delete(client, db_session):
    _make_staff(db_session)
    csrf = _login(client)
    loc = _make_location(client, csrf)
    title = _make_title(client, csrf)
    copy = client.post(f"/api/v1/titles/{title['id']}/copies", headers=_h(csrf), json={"location_id": loc["id"]}).json()
    # Simulate a loan by setting checked_out directly.
    row = db_session.scalar(select(Copy).where(Copy.id == copy["id"]))
    row.status = CopyStatus.checked_out
    db_session.commit()

    assert client.patch(f"/api/v1/copies/{copy['id']}/status", headers=_h(csrf), json={"status": "available"}).status_code == 409
    assert client.delete(f"/api/v1/copies/{copy['id']}", headers=_h(csrf)).status_code == 409


# --- US3 ----------------------------------------------------------------------
def test_delete_copy_and_title_rules(client, db_session):
    _make_staff(db_session)
    csrf = _login(client)
    loc = _make_location(client, csrf)
    title = _make_title(client, csrf)
    copy = client.post(f"/api/v1/titles/{title['id']}/copies", headers=_h(csrf), json={"location_id": loc["id"]}).json()

    # Title with a copy cannot be deleted
    assert client.delete(f"/api/v1/titles/{title['id']}", headers=_h(csrf)).status_code == 409
    # Delete the copy, then the title
    assert client.delete(f"/api/v1/copies/{copy['id']}", headers=_h(csrf)).status_code == 204
    assert client.delete(f"/api/v1/titles/{title['id']}", headers=_h(csrf)).status_code == 204


def test_catalog_mutations_require_csrf(client, db_session):
    _make_staff(db_session)
    _login(client)
    assert client.post("/api/v1/titles", json={"name": "NoCsrf"}).status_code == 403
