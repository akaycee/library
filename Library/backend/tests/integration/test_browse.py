"""Integration tests for Catalog Search & Browse (F5)."""

from sqlalchemy import select

from src.core.security import hash_password
from src.models.base import CopyStatus, Role, UserStatus
from src.models.copy import Copy
from src.models.user import User


def _staff(db, username="lib"):
    u = User(
        username=username,
        username_normalized=username.casefold(),
        password_hash=hash_password("abcd1234"),
        role=Role.librarian,
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


def _seed_catalog(client, csrf):
    h = {"X-CSRF-Token": csrf}
    loc = client.post("/api/v1/locations", headers=h, json={"name": "Room"}).json()
    t1 = client.post("/api/v1/titles", headers=h, json={"name": "Charlotte's Web", "author": "E.B. White", "isbn": "111"}).json()
    t2 = client.post("/api/v1/titles", headers=h, json={"name": "The Hobbit", "author": "Tolkien", "isbn": "222"}).json()
    # t1: 2 copies (1 available, 1 lost); t2: 1 available
    c1 = client.post(f"/api/v1/titles/{t1['id']}/copies", headers=h, json={"location_id": loc["id"]}).json()
    client.post(f"/api/v1/titles/{t1['id']}/copies", headers=h, json={"location_id": loc["id"]})
    client.post(f"/api/v1/titles/{t2['id']}/copies", headers=h, json={"location_id": loc["id"]})
    return loc, t1, t2, c1


def test_browse_requires_authentication(client):
    assert client.get("/api/v1/browse").status_code == 401


def test_borrower_can_browse_with_availability(client, db_session):
    _staff(db_session)
    csrf = _login(client, "lib")
    _loc, t1, _t2, c1 = _seed_catalog(client, csrf)
    # Mark one copy of t1 as lost -> 1 of 2 available.
    row = db_session.scalar(select(Copy).where(Copy.id == c1["id"]))
    # find the other copy of t1 and leave it available; set this one lost
    row.status = CopyStatus.lost
    db_session.commit()

    # A borrower browses.
    client.post("/api/v1/auth/register", json={"username": "bo", "password": "abcd1234"})
    client.post("/api/v1/auth/login", json={"username": "bo", "password": "abcd1234"})
    items = client.get("/api/v1/browse").json()
    by_name = {i["name"]: i for i in items}
    assert by_name["Charlotte's Web"]["total_count"] == 2
    assert by_name["Charlotte's Web"]["available_count"] == 1
    assert by_name["The Hobbit"]["available_count"] == 1


def test_browse_hides_barcodes_and_locations(client, db_session):
    _staff(db_session)
    csrf = _login(client, "lib")
    _seed_catalog(client, csrf)
    items = client.get("/api/v1/browse").json()
    assert items, "expected some titles"
    for i in items:
        assert "barcode" not in i
        assert "location_id" not in i
        assert "location_path" not in i


def test_search_matches_name_author_isbn(client, db_session):
    _staff(db_session)
    csrf = _login(client, "lib")
    _seed_catalog(client, csrf)

    # by name
    r = client.get("/api/v1/browse", params={"q": "hobbit"}).json()
    assert [i["name"] for i in r] == ["The Hobbit"]
    # by author
    r = client.get("/api/v1/browse", params={"q": "white"}).json()
    assert [i["name"] for i in r] == ["Charlotte's Web"]
    # by isbn
    r = client.get("/api/v1/browse", params={"q": "222"}).json()
    assert [i["name"] for i in r] == ["The Hobbit"]
    # no match
    assert client.get("/api/v1/browse", params={"q": "zzz"}).json() == []
    # empty query returns all
    assert len(client.get("/api/v1/browse", params={"q": ""}).json()) == 2
