"""Integration tests for the Librarian Dashboard (F9)."""

from datetime import timedelta

from sqlalchemy import select

from src.core.security import hash_password
from src.models.base import Role, UserStatus
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


def _seed_copy(client, csrf, *, title="Book", room="Room"):
    h = {"X-CSRF-Token": csrf}
    loc = client.post("/api/v1/locations", headers=h, json={"name": room}).json()
    t = client.post("/api/v1/titles", headers=h, json={"name": title}).json()
    copy = client.post(f"/api/v1/titles/{t['id']}/copies", headers=h, json={"location_id": loc["id"]}).json()
    return copy


def test_summary_reflects_collection_and_circulation(client, db_session):
    _user(db_session, "lib", Role.librarian)
    _user(db_session, "borrower1", Role.borrower)
    csrf = _login(client, "lib")
    h = {"X-CSRF-Token": csrf}
    copy = _seed_copy(client, csrf)

    # Baseline: one title, one copy, all available, nothing on loan.
    s = client.get("/api/v1/dashboard/summary").json()
    assert s["titles"] == 1
    assert s["copies"] == 1
    assert s["available"] == 1
    assert s["on_loan"] == 0
    assert s["overdue"] == 0
    assert s["active_borrowers"] == 0

    # Check out -> on_loan up, available down, one active borrower.
    client.post("/api/v1/loans", headers=h, json={"barcode": copy["barcode"], "borrower_username": "borrower1", "loan_period_days": 14})
    s = client.get("/api/v1/dashboard/summary").json()
    assert s["on_loan"] == 1
    assert s["available"] == 0
    assert s["active_borrowers"] == 1
    # Recent activity records the checkout, newest-first.
    assert s["recent_activity"]
    assert s["recent_activity"][0]["action"] == "loan.checkout"


def test_overdue_panel_lists_and_returns(client, db_session):
    _user(db_session, "lib", Role.librarian)
    _user(db_session, "borrower1", Role.borrower)
    csrf = _login(client, "lib")
    h = {"X-CSRF-Token": csrf}
    copy = _seed_copy(client, csrf)

    loan = client.post("/api/v1/loans", headers=h, json={"barcode": copy["barcode"], "borrower_username": "borrower1", "loan_period_days": 14}).json()
    # Force it overdue.
    row = db_session.scalar(select(Loan).where(Loan.id == loan["id"]))
    row.due_at = row.borrowed_at - timedelta(days=1)
    db_session.commit()

    s = client.get("/api/v1/dashboard/summary").json()
    assert s["overdue"] == 1
    assert len(s["overdue_loans"]) == 1
    assert s["overdue_loans"][0]["borrower_username"] == "borrower1"
    assert s["overdue_loans"][0]["overdue"] is True

    # Return from the desk clears it.
    client.post(f"/api/v1/loans/{loan['id']}/return", headers=h)
    s = client.get("/api/v1/dashboard/summary").json()
    assert s["overdue"] == 0
    assert s["overdue_loans"] == []
    assert s["available"] == 1


def test_dashboard_is_staff_only(client, db_session):
    _user(db_session, "borrower1", Role.borrower)
    _login(client, "borrower1")
    assert client.get("/api/v1/dashboard/summary").status_code == 403
