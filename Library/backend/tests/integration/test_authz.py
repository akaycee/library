"""Authorization tests: non-administrators cannot access user management (US2)."""


def _register_and_login(client, username, password="abcd1234"):
    client.post("/api/v1/auth/register", json={"username": username, "password": password})
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return client.cookies.get("library_csrf")


def test_borrower_cannot_list_users(client):
    _register_and_login(client, "bortest")
    resp = client.get("/api/v1/admin/users")
    assert resp.status_code == 403


def test_borrower_cannot_create_users(client):
    csrf = _register_and_login(client, "bortest2")
    resp = client.post(
        "/api/v1/admin/users",
        headers={"X-CSRF-Token": csrf},
        json={"username": "x", "password": "abcd1234", "role": "administrator"},
    )
    assert resp.status_code == 403


def test_unauthenticated_cannot_list_users(client):
    resp = client.get("/api/v1/admin/users")
    assert resp.status_code == 401
