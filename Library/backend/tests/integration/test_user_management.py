"""Integration tests for administrator user management (US2)."""

from src.core.security import hash_password
from src.models.base import Role, UserStatus
from src.models.user import User


def _make_admin(db, username="root", password="adminpass1"):
    admin = User(
        username=username,
        username_normalized=username.casefold(),
        password_hash=hash_password(password),
        role=Role.administrator,
        status=UserStatus.active,
        force_password_change=False,
    )
    db.add(admin)
    db.commit()
    return admin


def _login(client, username, password):
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return client.cookies.get("library_csrf")


def test_admin_creates_librarian_and_lists_users(client, db_session):
    _make_admin(db_session)
    csrf = _login(client, "root", "adminpass1")

    created = client.post(
        "/api/v1/admin/users",
        headers={"X-CSRF-Token": csrf},
        json={"username": "libby", "password": "abcd1234", "role": "librarian"},
    )
    assert created.status_code == 201
    assert created.json()["role"] == "librarian"

    listing = client.get("/api/v1/admin/users")
    assert listing.status_code == 200
    usernames = {u["username"]: u["role"] for u in listing.json()}
    assert usernames.get("libby") == "librarian"
    assert usernames.get("root") == "administrator"


def test_admin_changes_role(client, db_session):
    _make_admin(db_session)
    csrf = _login(client, "root", "adminpass1")
    created = client.post(
        "/api/v1/admin/users",
        headers={"X-CSRF-Token": csrf},
        json={"username": "borrower1", "password": "abcd1234", "role": "borrower"},
    )
    uid = created.json()["id"]
    changed = client.patch(
        f"/api/v1/admin/users/{uid}/role",
        headers={"X-CSRF-Token": csrf},
        json={"role": "librarian"},
    )
    assert changed.status_code == 200
    assert changed.json()["role"] == "librarian"


def test_cannot_demote_last_administrator(client, db_session):
    admin = _make_admin(db_session)
    csrf = _login(client, "root", "adminpass1")
    resp = client.patch(
        f"/api/v1/admin/users/{admin.id}/role",
        headers={"X-CSRF-Token": csrf},
        json={"role": "borrower"},
    )
    assert resp.status_code == 409


def test_cannot_deactivate_last_administrator(client, db_session):
    admin = _make_admin(db_session)
    csrf = _login(client, "root", "adminpass1")
    resp = client.patch(
        f"/api/v1/admin/users/{admin.id}/status",
        headers={"X-CSRF-Token": csrf},
        json={"status": "deactivated"},
    )
    assert resp.status_code == 409


def test_deactivation_revokes_sessions(client, db_session):
    _make_admin(db_session)
    csrf = _login(client, "root", "adminpass1")
    # A self-registered borrower gets a full session immediately (no forced change).
    client.post("/api/v1/auth/register", json={"username": "user2", "password": "abcd1234"})
    # user2 logs in on a separate client session.
    from fastapi.testclient import TestClient
    from src.main import app

    with TestClient(app) as other:
        other.post("/api/v1/auth/login", json={"username": "user2", "password": "abcd1234"})
        assert other.get("/api/v1/auth/me").status_code == 200
        uid = None
        for u in client.get("/api/v1/admin/users").json():
            if u["username"] == "user2":
                uid = u["id"]
        assert uid is not None
        deac = client.patch(
            f"/api/v1/admin/users/{uid}/status",
            headers={"X-CSRF-Token": csrf},
            json={"status": "deactivated"},
        )
        assert deac.status_code == 200
        # The deactivated user's session is now rejected.
        assert other.get("/api/v1/auth/me").status_code == 401
