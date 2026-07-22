"""Integration tests for the email-free password reset flow (US3)."""

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


def _admin_csrf(client):
    resp = client.post("/api/v1/auth/login", json={"username": "root", "password": "adminpass1"})
    assert resp.status_code == 200
    return client.cookies.get("library_csrf")


def _register(client, username, password="abcd1234"):
    assert client.post(
        "/api/v1/auth/register", json={"username": username, "password": password}
    ).status_code == 201


def test_full_reset_flow(client, db_session):
    _make_admin(db_session)
    _register(client, "carol")

    # 1. Carol requests a reset (always 202).
    r = client.post("/api/v1/auth/reset-requests", json={"username": "carol"})
    assert r.status_code == 202

    # 2. Admin sees it in the queue and issues a temp password.
    csrf = _admin_csrf(client)
    queue = client.get("/api/v1/admin/reset-requests").json()
    assert any(item["username"] == "carol" for item in queue)
    req_id = next(item["id"] for item in queue if item["username"] == "carol")
    issued = client.post(
        f"/api/v1/admin/reset-requests/{req_id}/issue", headers={"X-CSRF-Token": csrf}
    )
    assert issued.status_code == 200
    temp = issued.json()["temporary_password"]
    # Log the admin out so we act as Carol on the same client.
    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})

    # 3. Carol logs in with the temporary password -> restricted session.
    tlog = client.post(
        "/api/v1/auth/login-temporary", json={"username": "carol", "temporary_password": temp}
    )
    assert tlog.status_code == 200
    assert tlog.json()["force_password_change"] is True
    new_csrf = client.cookies.get("library_csrf")

    # Restricted session cannot reach normal endpoints.
    assert client.get("/api/v1/auth/me").status_code == 401

    # 4. Carol sets a new password (forced change; no current password needed).
    changed = client.post(
        "/api/v1/auth/change-password",
        headers={"X-CSRF-Token": new_csrf},
        json={"new_password": "newpass12"},
    )
    assert changed.status_code == 200
    assert changed.json()["force_password_change"] is False

    # Now a full session works.
    assert client.get("/api/v1/auth/me").status_code == 200

    # 5. Old password no longer works; new one does.
    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": client.cookies.get("library_csrf")})
    assert client.post(
        "/api/v1/auth/login", json={"username": "carol", "password": "abcd1234"}
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login", json={"username": "carol", "password": "newpass12"}
    ).status_code == 200


def test_temporary_password_is_single_use(client, db_session):
    _make_admin(db_session)
    _register(client, "dave")
    client.post("/api/v1/auth/reset-requests", json={"username": "dave"})
    csrf = _admin_csrf(client)
    queue = client.get("/api/v1/admin/reset-requests").json()
    req_id = next(i["id"] for i in queue if i["username"] == "dave")
    temp = client.post(
        f"/api/v1/admin/reset-requests/{req_id}/issue", headers={"X-CSRF-Token": csrf}
    ).json()["temporary_password"]
    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})

    # First temp login consumes it.
    assert client.post(
        "/api/v1/auth/login-temporary", json={"username": "dave", "temporary_password": temp}
    ).status_code == 200
    client.cookies.clear()
    # Second attempt with the same temp password is rejected.
    assert client.post(
        "/api/v1/auth/login-temporary", json={"username": "dave", "temporary_password": temp}
    ).status_code == 401


def test_reset_request_does_not_reveal_username_existence(client):
    # Unknown username returns the same 202 as a known one.
    assert client.post(
        "/api/v1/auth/reset-requests", json={"username": "nobody-here"}
    ).status_code == 202


def test_reset_queue_requires_admin(client):
    _register(client, "erin")
    client.post("/api/v1/auth/login", json={"username": "erin", "password": "abcd1234"})
    assert client.get("/api/v1/admin/reset-requests").status_code == 403


def test_invalid_temporary_password_rejected(client, db_session):
    _register(client, "frank")
    assert client.post(
        "/api/v1/auth/login-temporary",
        json={"username": "frank", "temporary_password": "not-a-real-temp"},
    ).status_code == 401
