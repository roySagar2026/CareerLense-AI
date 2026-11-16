from __future__ import annotations

from tests.conftest import PASSWORD, auth_headers, register

CSRF = {"X-Requested-With": "CareerLens"}


def test_register_login_me_and_weak_password(client):
    bad = client.post("/api/v1/auth/register", json={"email": "x@example.com", "password": "short1"})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "validation_error"

    body = register(client)
    assert body["token_type"] == "bearer" and body["user"]["email"] == "asha@example.com"
    assert "password" not in str(body)

    dup = client.post("/api/v1/auth/register", json={"email": "ASHA@example.com", "password": PASSWORD})
    assert dup.status_code == 409

    login = client.post("/api/v1/auth/login", json={"email": "asha@example.com", "password": PASSWORD})
    assert login.status_code == 200
    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert me.status_code == 200 and me.json()["full_name"] == "Asha"


def test_wrong_password_and_unauthenticated(client):
    register(client)
    wrong = client.post("/api/v1/auth/login", json={"email": "asha@example.com", "password": "nope-nope-1234"})
    assert wrong.status_code == 401
    assert client.get("/api/v1/users/me").status_code == 401
    assert client.get("/api/v1/users/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_login_rate_limit(client):
    register(client)
    for _ in range(8):
        client.post("/api/v1/auth/login", json={"email": "asha@example.com", "password": "wrong-pass-123"})
    blocked = client.post("/api/v1/auth/login", json={"email": "asha@example.com", "password": PASSWORD})
    assert blocked.status_code == 429 and blocked.json()["error"]["code"] == "rate_limited"


def test_refresh_rotation_and_reuse_detection(client):
    register(client)
    first_cookie = client.cookies.get("cl_refresh")
    assert first_cookie

    assert client.post("/api/v1/auth/refresh").status_code == 403  # missing CSRF header

    rotated = client.post("/api/v1/auth/refresh", headers=CSRF)
    assert rotated.status_code == 200
    second_cookie = client.cookies.get("cl_refresh")
    assert second_cookie and second_cookie != first_cookie

    # Replaying the already-rotated token is treated as theft: the whole family is revoked.
    client.cookies.set("cl_refresh", first_cookie, path="/api/v1/auth")
    assert client.post("/api/v1/auth/refresh", headers=CSRF).status_code == 401
    client.cookies.set("cl_refresh", second_cookie, path="/api/v1/auth")
    assert client.post("/api/v1/auth/refresh", headers=CSRF).status_code == 401


def test_logout_revokes_session(client):
    register(client)
    assert client.post("/api/v1/auth/logout", headers=CSRF).status_code == 204
    assert client.post("/api/v1/auth/refresh", headers=CSRF).status_code == 401


def test_forgot_password_never_reveals_account(client):
    register(client)
    known = client.post("/api/v1/auth/forgot-password", json={"email": "asha@example.com"})
    unknown = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    bad = client.post("/api/v1/auth/reset-password", json={"token": "x" * 40, "new_password": PASSWORD})
    assert bad.status_code == 400


def test_change_password_and_delete_account(client):
    headers = auth_headers(client)
    new_password = "Another-Pass-77"
    wrong = client.post(
        "/api/v1/users/me/password",
        json={"current_password": "bad-pass-1234", "new_password": new_password},
        headers=headers,
    )
    assert wrong.status_code == 403
    ok = client.post(
        "/api/v1/users/me/password", json={"current_password": PASSWORD, "new_password": new_password}, headers=headers
    )
    assert ok.status_code == 204
    assert (
        client.post("/api/v1/auth/login", json={"email": "asha@example.com", "password": new_password}).status_code
        == 200
    )

    assert (
        client.request("DELETE", "/api/v1/users/me", json={"password": "bad-pass-1234"}, headers=headers).status_code
        == 403
    )
    assert (
        client.request("DELETE", "/api/v1/users/me", json={"password": new_password}, headers=headers).status_code
        == 204
    )
    assert (
        client.post("/api/v1/auth/login", json={"email": "asha@example.com", "password": new_password}).status_code
        == 401
    )
