"""Integration tests for Borrowing & Returns (F6)."""

from datetime import timedelta

from sqlalchemy import select

from src.core.security import hash_password
from src.models.base import CopyStatus, Role, UserStatus
from src.models.copy import Copy
from src.models.loan import Loan
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


def _seed_copy(client, csrf):
    h = {"X-CSRF-Token": csrf}
    loc = client.post("/api/v1/locations", headers=h, json={"name": "Room"}).json()
    title = client.post("/api/v1/titles", headers=h, json={"name": "Book"}).json()
    copy = client.post(f"/api/v1/titles/{title['id']}/copies", headers=h, json={"location_id": loc["id"]}).json()
    return copy


def test_checkout_and_return(client, db_session):
    _user(db_session, "lib", Role.librarian)
    _user(db_session, "borrower1", Role.borrower)
    csrf = _login(client, "lib")
    h = {"X-CSRF-Token": csrf}
    copy = _seed_copy(client, csrf)

    out = client.post("/api/v1/loans", headers=h, json={"barcode": copy["barcode"], "borrower_username": "borrower1", "loan_period_days": 14})
    assert out.status_code == 201
    loan = out.json()
    assert loan["overdue"] is False
    # Copy is now checked out.
    row = db_session.scalar(select(Copy).where(Copy.id == copy["id"]))
    assert row.status == CopyStatus.checked_out
    # Availability reflects it.
    items = {i["name"]: i for i in client.get("/api/v1/browse").json()}
    assert items["Book"]["available_count"] == 0

    # Return.
    ret = client.post(f"/api/v1/loans/{loan['id']}/return", headers=h)
    assert ret.status_code == 200
    row = db_session.scalar(select(Copy).where(Copy.id == copy["id"]))
    assert row.status == CopyStatus.available


def test_checkout_rejects_unavailable_and_unknown(client, db_session):
    _user(db_session, "lib", Role.librarian)
    _user(db_session, "borrower1", Role.borrower)
    csrf = _login(client, "lib")
    h = {"X-CSRF-Token": csrf}
    copy = _seed_copy(client, csrf)

    # Unknown barcode
    assert client.post("/api/v1/loans", headers=h, json={"barcode": "NOPE", "borrower_username": "borrower1", "loan_period_days": 7}).status_code == 404
    # Unknown borrower
    assert client.post("/api/v1/loans", headers=h, json={"barcode": copy["barcode"], "borrower_username": "ghost", "loan_period_days": 7}).status_code == 404
    # Bad period
    assert client.post("/api/v1/loans", headers=h, json={"barcode": copy["barcode"], "borrower_username": "borrower1", "loan_period_days": 0}).status_code == 422
    # Check out, then a second checkout of the same copy fails
    client.post("/api/v1/loans", headers=h, json={"barcode": copy["barcode"], "borrower_username": "borrower1", "loan_period_days": 7})
    assert client.post("/api/v1/loans", headers=h, json={"barcode": copy["barcode"], "borrower_username": "borrower1", "loan_period_days": 7}).status_code == 409


def test_borrower_cannot_check_out(client, db_session):
    _user(db_session, "lib", Role.librarian)
    csrf = _login(client, "lib")
    copy = _seed_copy(client, csrf)
    _user(db_session, "bo", Role.borrower)
    bcsrf = _login(client, "bo")
    resp = client.post("/api/v1/loans", headers={"X-CSRF-Token": bcsrf}, json={"barcode": copy["barcode"], "borrower_username": "bo", "loan_period_days": 7})
    assert resp.status_code == 403


def test_renew_and_overdue(client, db_session):
    _user(db_session, "lib", Role.librarian)
    _user(db_session, "borrower1", Role.borrower)
    csrf = _login(client, "lib")
    h = {"X-CSRF-Token": csrf}
    copy = _seed_copy(client, csrf)
    loan = client.post("/api/v1/loans", headers=h, json={"barcode": copy["barcode"], "borrower_username": "borrower1", "loan_period_days": 7}).json()

    # Renew extends due date + count
    r = client.post(f"/api/v1/loans/{loan['id']}/renew", headers=h, json={"days": 7})
    assert r.status_code == 200 and r.json()["renewal_count"] == 1

    # Force overdue and confirm flag + renewal refusal
    row = db_session.scalar(select(Loan).where(Loan.id == loan["id"]))
    row.due_at = row.due_at - timedelta(days=30)
    db_session.commit()
    active = client.get("/api/v1/loans", headers=h).json()
    assert active[0]["overdue"] is True
    overdue = client.get("/api/v1/loans", headers=h, params={"status_filter": "overdue"}).json()
    assert len(overdue) == 1
    assert client.post(f"/api/v1/loans/{loan['id']}/renew", headers=h, json={"days": 7}).status_code == 409


def test_my_loans(client, db_session):
    _user(db_session, "lib", Role.librarian)
    _user(db_session, "borrower1", Role.borrower)
    csrf = _login(client, "lib")
    h = {"X-CSRF-Token": csrf}
    copy = _seed_copy(client, csrf)
    client.post("/api/v1/loans", headers=h, json={"barcode": copy["barcode"], "borrower_username": "borrower1", "loan_period_days": 7})

    # Borrower sees their loan
    bcsrf = _login(client, "borrower1")
    mine = client.get("/api/v1/loans/mine").json()
    assert len(mine) == 1 and mine[0]["title_name"] == "Book"
    # Staff (lib) has none of their own
    _login(client, "lib")
    assert client.get("/api/v1/loans/mine").json() == []
