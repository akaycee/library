"""Integration tests for staff borrower quick-create (F6 desk enhancement)."""

from sqlalchemy import select

from src.core.security import hash_password, verify_password
from src.models.base import Role, UserStatus
from src.models.user import User


def _user(db, username, role=Role.librarian):
    u = User(
        username=username,
        username_normalized=username.casefold(),
        password_hash=hash_password("abcd1234"),
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


def test_staff_creates_borrower_with_generated_password(client, db_session):
    _user(db_session, "lib", Role.librarian)
    csrf = _login(client, "lib")
    resp = client.post(
        "/api/v1/borrowers", headers={"X-CSRF-Token": csrf}, json={"username": "newbie"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["role"] == "borrower"
    assert body["temporary_password"]  # returned once

    # The generated password actually works and forces a change on first login.
    row = db_session.scalar(select(User).where(User.username_normalized == "newbie"))
    assert row is not None
    assert row.force_password_change is True
    assert verify_password(body["temporary_password"], row.password_hash)


def test_staff_creates_borrower_with_chosen_password(client, db_session):
    _user(db_session, "lib", Role.librarian)
    csrf = _login(client, "lib")
    resp = client.post(
        "/api/v1/borrowers",
        headers={"X-CSRF-Token": csrf},
        json={"username": "chosen", "password": "Sup3rSecret!"},
    )
    assert resp.status_code == 201
    assert resp.json()["temporary_password"] is None
    row = db_session.scalar(select(User).where(User.username_normalized == "chosen"))
    assert verify_password("Sup3rSecret!", row.password_hash)


def test_duplicate_username_is_rejected(client, db_session):
    _user(db_session, "lib", Role.librarian)
    _user(db_session, "dupe", Role.borrower)
    csrf = _login(client, "lib")
    resp = client.post(
        "/api/v1/borrowers", headers={"X-CSRF-Token": csrf}, json={"username": "dupe"}
    )
    assert resp.status_code == 409


def test_weak_chosen_password_is_rejected(client, db_session):
    _user(db_session, "lib", Role.librarian)
    csrf = _login(client, "lib")
    resp = client.post(
        "/api/v1/borrowers",
        headers={"X-CSRF-Token": csrf},
        json={"username": "weakpw", "password": "123"},
    )
    assert resp.status_code == 422


def test_borrower_cannot_create_borrowers(client, db_session):
    _user(db_session, "bo", Role.borrower)
    csrf = _login(client, "bo")
    resp = client.post(
        "/api/v1/borrowers", headers={"X-CSRF-Token": csrf}, json={"username": "nope"}
    )
    assert resp.status_code == 403
