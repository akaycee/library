"""Contract tests for the auth endpoints (register/login/logout/me)."""


def test_register_creates_borrower(client):
    resp = client.post("/api/v1/auth/register", json={"username": "alice", "password": "abcd1234"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "alice"
    assert body["role"] == "borrower"
    assert "id" in body


def test_register_duplicate_username_conflicts(client):
    client.post("/api/v1/auth/register", json={"username": "bob", "password": "abcd1234"})
    resp = client.post("/api/v1/auth/register", json={"username": "BOB", "password": "abcd1234"})
    assert resp.status_code == 409


def test_register_weak_password_rejected(client):
    resp = client.post("/api/v1/auth/register", json={"username": "carol", "password": "weak"})
    assert resp.status_code == 422


def test_login_success_sets_cookies(client):
    client.post("/api/v1/auth/register", json={"username": "dave", "password": "abcd1234"})
    resp = client.post("/api/v1/auth/login", json={"username": "dave", "password": "abcd1234"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "borrower"
    assert "library_session" in resp.cookies
    assert "library_csrf" in resp.cookies


def test_login_wrong_password_is_401(client):
    client.post("/api/v1/auth/register", json={"username": "erin", "password": "abcd1234"})
    resp = client.post("/api/v1/auth/login", json={"username": "erin", "password": "nope0000"})
    assert resp.status_code == 401


def test_login_unknown_user_is_indistinguishable_401(client):
    resp = client.post("/api/v1/auth/login", json={"username": "ghost", "password": "abcd1234"})
    assert resp.status_code == 401


def test_me_requires_authentication(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
