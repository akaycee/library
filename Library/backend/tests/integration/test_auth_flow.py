"""Integration test for the register -> login -> me -> logout journey, including
session rotation on login and revocation on logout, and CSRF on logout."""


def test_full_auth_flow(client):
    # Register
    reg = client.post("/api/v1/auth/register", json={"username": "frank", "password": "abcd1234"})
    assert reg.status_code == 201

    # Login establishes a session
    login = client.post("/api/v1/auth/login", json={"username": "frank", "password": "abcd1234"})
    assert login.status_code == 200
    csrf = login.cookies["library_csrf"]

    # Authenticated 'me' works
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "frank"

    # Logout without CSRF header is rejected
    bad = client.post("/api/v1/auth/logout")
    assert bad.status_code == 403

    # Logout with CSRF header succeeds and revokes the session
    out = client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})
    assert out.status_code == 200

    # After logout the session is no longer valid
    me_after = client.get("/api/v1/auth/me")
    assert me_after.status_code == 401


def test_login_rotates_session(client):
    client.post("/api/v1/auth/register", json={"username": "gina", "password": "abcd1234"})
    first = client.post("/api/v1/auth/login", json={"username": "gina", "password": "abcd1234"})
    token1 = first.cookies["library_session"]
    second = client.post("/api/v1/auth/login", json={"username": "gina", "password": "abcd1234"})
    token2 = second.cookies["library_session"]
    assert token1 != token2
