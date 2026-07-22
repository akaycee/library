"""Regression tests for the independent security/correctness review fixes."""

import re

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.core import db as db_module
from src.core.config import Settings
from src.models.base import Role, UserStatus
from src.models.loan import Loan
from src.models.user import User
from src.services import reset as reset_service


def _user(db, username, role=Role.librarian, force=False):
    u = User(
        username=username,
        username_normalized=username.casefold(),
        password_hash=__import__("src.core.security", fromlist=["hash_password"]).hash_password("abcd1234"),
        role=role,
        status=UserStatus.active,
        force_password_change=force,
    )
    db.add(u)
    db.commit()
    return u


def _login(client, username, password="abcd1234"):
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200
    return client.cookies.get("library_csrf")


def _seed_copy(client, csrf, title="Book", room="Room"):
    h = {"X-CSRF-Token": csrf}
    loc = client.post("/api/v1/locations", headers=h, json={"name": room}).json()
    t = client.post("/api/v1/titles", headers=h, json={"name": title}).json()
    return client.post(f"/api/v1/titles/{t['id']}/copies", headers=h, json={"location_id": loc["id"]}).json()


# C1 -------------------------------------------------------------------------
def test_db_rejects_second_active_loan_for_a_copy(client, db_session):
    _user(db_session, "lib", Role.librarian)
    _user(db_session, "bor", Role.borrower)
    csrf = _login(client, "lib")
    copy = _seed_copy(client, csrf)
    client.post("/api/v1/loans", headers={"X-CSRF-Token": csrf}, json={"barcode": copy["barcode"], "borrower_username": "bor", "loan_period_days": 7})

    # Directly attempt a second active loan on the same copy -> unique index fires.
    bor = db_session.scalar(select(User).where(User.username_normalized == "bor"))
    db_session.add(Loan(copy_id=copy["id"], borrower_id=bor.id, due_at=__import__("datetime").datetime.now()))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# C2 -------------------------------------------------------------------------
def test_forced_password_change_blocks_full_api(client, db_session):
    _user(db_session, "root", Role.administrator)
    csrf = _login(client, "root")
    # Admin creates a user (force_password_change defaults True).
    client.post("/api/v1/admin/users", headers={"X-CSRF-Token": csrf}, json={"username": "fresh", "password": "abcd1234", "role": "librarian"})

    from fastapi.testclient import TestClient
    from src.main import app

    with TestClient(app) as other:
        other.post("/api/v1/auth/login", json={"username": "fresh", "password": "abcd1234"})
        # Restricted session: cannot reach the normal API.
        assert other.get("/api/v1/auth/me").status_code == 401
        assert other.get("/api/v1/titles").status_code == 401
        # After changing the password, a full session is granted.
        ccsrf = other.cookies.get("library_csrf")
        resp = other.post("/api/v1/auth/change-password", headers={"X-CSRF-Token": ccsrf}, json={"new_password": "Brandnew123"})
        assert resp.status_code == 200
        assert other.get("/api/v1/auth/me").status_code == 200


# C3 -------------------------------------------------------------------------
def test_encryption_enforced_when_required(monkeypatch):
    settings = Settings(require_encryption=True, db_key=None)
    monkeypatch.setattr(db_module, "get_settings", lambda: settings)
    with pytest.raises(db_module.EncryptionNotConfiguredError):
        db_module.enforce_encryption_at_rest()


def test_encryption_not_enforced_when_disabled(monkeypatch):
    settings = Settings(require_encryption=False, db_key=None)
    monkeypatch.setattr(db_module, "get_settings", lambda: settings)
    db_module.enforce_encryption_at_rest()  # must not raise


# H5 -------------------------------------------------------------------------
def test_superseded_temp_password_is_unusable(client, db_session):
    admin = _user(db_session, "root", Role.administrator)
    target = _user(db_session, "victim", Role.borrower)
    reset_service.submit_request(db_session, username="victim", client="1.1.1.1")
    db_session.commit()
    req = db_session.scalars(select(__import__("src.models.reset", fromlist=["PasswordResetRequest"]).PasswordResetRequest)).first()

    first, _ = reset_service.issue_temporary_password(db_session, actor_id=admin.id, request_id=req.id)
    db_session.commit()
    second, _ = reset_service.issue_temporary_password(db_session, actor_id=admin.id, request_id=req.id)
    db_session.commit()

    # The older password no longer works; the newest one does.
    with pytest.raises(reset_service.InvalidTemporaryPasswordError):
        reset_service.consume_temporary_login(db_session, username="victim", temporary_password=first)
    user = reset_service.consume_temporary_login(db_session, username="victim", temporary_password=second)
    assert user.id == target.id
    db_session.commit()

    # Completing the reset invalidates any lingering grants.
    reset_service.complete_reset(db_session, user=target)
    db_session.commit()
    with pytest.raises(reset_service.InvalidTemporaryPasswordError):
        reset_service.consume_temporary_login(db_session, username="victim", temporary_password=second)


# H6 -------------------------------------------------------------------------
def test_soft_delete_copy_with_returned_loan(client, db_session):
    _user(db_session, "lib", Role.librarian)
    _user(db_session, "bor", Role.borrower)
    csrf = _login(client, "lib")
    h = {"X-CSRF-Token": csrf}
    copy = _seed_copy(client, csrf)
    loan = client.post("/api/v1/loans", headers=h, json={"barcode": copy["barcode"], "borrower_username": "bor", "loan_period_days": 7}).json()
    client.post(f"/api/v1/loans/{loan['id']}/return", headers=h)

    # Previously a FK error; soft delete now succeeds and hides the copy.
    resp = client.delete(f"/api/v1/copies/{copy['id']}", headers=h)
    assert resp.status_code == 204
    title_id = client.get("/api/v1/titles").json()[0]["id"]
    detail = client.get(f"/api/v1/titles/{title_id}").json()
    assert all(c["id"] != copy["id"] for c in detail["copies"])


# M13 ------------------------------------------------------------------------
def test_checkout_requires_borrower_role(client, db_session):
    _user(db_session, "lib", Role.librarian)
    _user(db_session, "lib2", Role.librarian)
    csrf = _login(client, "lib")
    copy = _seed_copy(client, csrf)
    # lib2 is staff, not a borrower -> refused.
    r = client.post("/api/v1/loans", headers={"X-CSRF-Token": csrf}, json={"barcode": copy["barcode"], "borrower_username": "lib2", "loan_period_days": 7})
    assert r.status_code == 404


def test_manual_nonnumeric_barcode_does_not_break_allocation(client, db_session):
    _user(db_session, "lib", Role.librarian)
    csrf = _login(client, "lib")
    h = {"X-CSRF-Token": csrf}
    loc = client.post("/api/v1/locations", headers=h, json={"name": "R"}).json()
    t = client.post("/api/v1/titles", headers=h, json={"name": "T"}).json()
    # A manual, non-numeric barcode that shares the auto prefix.
    client.post(f"/api/v1/titles/{t['id']}/copies", headers=h, json={"location_id": loc["id"], "barcode": "LIB-ZZZ"})
    # Auto allocation still yields a valid LIB-###### barcode.
    auto = client.post(f"/api/v1/titles/{t['id']}/copies", headers=h, json={"location_id": loc["id"]}).json()
    assert re.fullmatch(r"LIB-\d{6}", auto["barcode"])


def test_browse_treats_wildcards_literally(client, db_session):
    _user(db_session, "lib", Role.librarian)
    csrf = _login(client, "lib")
    h = {"X-CSRF-Token": csrf}
    client.post("/api/v1/titles", headers=h, json={"name": "50% Off Guide"})
    client.post("/api/v1/titles", headers=h, json={"name": "Plain Book"})
    # '%' must match literally, not as a wildcard (which would return everything).
    results = client.get("/api/v1/browse", params={"q": "50%"}).json()
    names = [r["name"] for r in results]
    assert "50% Off Guide" in names
    assert "Plain Book" not in names


# M12 ------------------------------------------------------------------------
def test_cross_origin_state_change_rejected(client, db_session):
    _user(db_session, "root", Role.administrator)
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "root", "password": "abcd1234"},
        headers={"Origin": "http://evil.example"},
    )
    assert r.status_code == 403
