"""Integration tests for the Audit Trail viewer (F7)."""

from src.core.security import hash_password
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


def _seed_activity(client, csrf):
    """Generate a few auditable actions: a title, a copy, and a borrower."""
    h = {"X-CSRF-Token": csrf}
    loc = client.post("/api/v1/locations", headers=h, json={"name": "Room"}).json()
    t = client.post("/api/v1/titles", headers=h, json={"name": "Book"}).json()
    client.post(f"/api/v1/titles/{t['id']}/copies", headers=h, json={"location_id": loc["id"]})
    client.post("/api/v1/borrowers", headers=h, json={"username": "reader"})


def test_list_is_newest_first_and_resolves_usernames(client, db_session):
    _user(db_session, "lib", Role.librarian)
    csrf = _login(client, "lib")
    _seed_activity(client, csrf)

    entries = client.get("/api/v1/audit").json()
    assert len(entries) >= 4
    # Newest-first: created_at is non-increasing.
    times = [e["created_at"] for e in entries]
    assert times == sorted(times, reverse=True)
    # Actor resolved to a username for staff-performed actions.
    lib_entries = [e for e in entries if e["actor"] == "lib"]
    assert lib_entries


def test_filter_by_action(client, db_session):
    _user(db_session, "lib", Role.librarian)
    csrf = _login(client, "lib")
    _seed_activity(client, csrf)

    only = client.get("/api/v1/audit", params={"action": "title.create"}).json()
    assert only
    assert all(e["action"] == "title.create" for e in only)


def test_filter_by_username(client, db_session):
    _user(db_session, "lib", Role.librarian)
    csrf = _login(client, "lib")
    _seed_activity(client, csrf)

    # The new borrower "reader" is the target of user.create.
    hits = client.get("/api/v1/audit", params={"q": "reader"}).json()
    assert hits
    assert all(e["actor"] == "reader" or e["target"] == "reader" for e in hits)
    # A username that matches nobody yields nothing.
    assert client.get("/api/v1/audit", params={"q": "nobody-xyz"}).json() == []


def test_actions_endpoint_lists_distinct(client, db_session):
    _user(db_session, "lib", Role.librarian)
    csrf = _login(client, "lib")
    _seed_activity(client, csrf)
    actions = client.get("/api/v1/audit/actions").json()
    assert "title.create" in actions
    assert actions == sorted(actions)


def test_paging_limits_results(client, db_session):
    _user(db_session, "lib", Role.librarian)
    csrf = _login(client, "lib")
    _seed_activity(client, csrf)
    page = client.get("/api/v1/audit", params={"limit": 2}).json()
    assert len(page) == 2


def test_audit_is_staff_only(client, db_session):
    _user(db_session, "bo", Role.borrower)
    _login(client, "bo")
    assert client.get("/api/v1/audit").status_code == 403
    assert client.get("/api/v1/audit/actions").status_code == 403
