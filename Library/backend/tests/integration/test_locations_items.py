"""The catalog copy-count makes location deletion refuse non-empty locations (F4 × F2)."""

from src.core.security import hash_password
from src.models.base import Role, UserStatus
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


def _login(client):
    resp = client.post("/api/v1/auth/login", json={"username": "lib", "password": "abcd1234"})
    assert resp.status_code == 200
    return client.cookies.get("library_csrf")


def test_location_with_copies_cannot_be_deleted(client, db_session):
    _staff(db_session)
    csrf = _login(client)
    h = {"X-CSRF-Token": csrf}

    loc = client.post("/api/v1/locations", headers=h, json={"name": "Shelf"}).json()
    title = client.post("/api/v1/titles", headers=h, json={"name": "Book"}).json()
    client.post(f"/api/v1/titles/{title['id']}/copies", headers=h, json={"location_id": loc["id"]})

    # Deleting the location now fails because it holds a copy.
    blocked = client.delete(f"/api/v1/locations/{loc['id']}", headers=h)
    assert blocked.status_code == 409
    assert "item" in blocked.json()["detail"].lower()
