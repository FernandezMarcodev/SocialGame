import re

from fastapi.testclient import TestClient

USERNAME = "ken2000"
EMAIL = "ken2000@example.com"
PASSWORD = "Passw0rd!"
NEW_PASSWORD = "NuevaPass2!"


def extract_token(body: str) -> str:
    match = re.search(r"[A-Za-z0-9_-]{40,}", body)
    assert match is not None, f"No se encontró token en: {body}"
    return match.group(0)


def register(client: TestClient, outbox, username=USERNAME, email=EMAIL, password=PASSWORD):
    resp = client.post("/api/v1/auth/register", json={
        "username": username, "email": email, "password": password,
    })
    assert resp.status_code == 201, resp.text
    return resp


def verified_login(client: TestClient, outbox, username=USERNAME, email=EMAIL, password=PASSWORD):
    register(client, outbox, username, email, password)
    token = extract_token(outbox.pop(0)[2])
    resp = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert resp.status_code == 200, resp.text
    resp = client.post("/api/v1/auth/login", json={"identifier": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_register_creates_unverified_user(client, outbox):
    resp = register(client, outbox)
    data = resp.json()
    assert data["username"] == USERNAME
    assert data["verified"] is False
    assert data["email"] == EMAIL
    assert data["profile_image_url"] == "/avatars/k.svg"
    assert len(outbox) == 1
    assert outbox[0][0] == EMAIL


def test_register_rejects_duplicate_username(client, outbox):
    register(client, outbox)
    resp = client.post("/api/v1/auth/register", json={
        "username": USERNAME.upper(), "email": "otro@example.com", "password": PASSWORD,
    })
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "USERNAME_TAKEN"


def test_register_rejects_duplicate_email(client, outbox):
    register(client, outbox)
    resp = client.post("/api/v1/auth/register", json={
        "username": "otro", "email": EMAIL, "password": PASSWORD,
    })
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "EMAIL_TAKEN"


def test_register_rejects_username_out_of_policy(client, outbox):
    resp = client.post("/api/v1/auth/register", json={
        "username": "ab", "email": EMAIL, "password": PASSWORD,
    })
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_register_rejects_weak_password(client, outbox):
    resp = client.post("/api/v1/auth/register", json={
        "username": USERNAME, "email": EMAIL, "password": "ABCDEFGH",
    })
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "password" in body["error"]["details"]


def test_full_flow_verify_and_login_and_me(client, outbox):
    token = verified_login(client, outbox)
    resp = client.get("/api/v1/users/me", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["username"] == USERNAME
    assert resp.json()["verified"] is True


def test_login_rejected_until_email_verified(client, outbox):
    register(client, outbox)
    resp = client.post("/api/v1/auth/login", json={"identifier": USERNAME, "password": PASSWORD})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


def test_login_wrong_password(client, outbox):
    register(client, outbox)
    token = extract_token(outbox.pop(0)[2])
    client.post("/api/v1/auth/verify-email", json={"token": token})
    resp = client.post("/api/v1/auth/login", json={"identifier": USERNAME, "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_blocks_after_max_attempts(client, outbox):
    register(client, outbox)
    token = extract_token(outbox.pop(0)[2])
    client.post("/api/v1/auth/verify-email", json={"token": token})
    for _ in range(4):
        resp = client.post("/api/v1/auth/login", json={"identifier": USERNAME, "password": "wrong"})
        assert resp.status_code == 401
    resp = client.post("/api/v1/auth/login", json={"identifier": USERNAME, "password": "wrong"})
    assert resp.status_code == 423
    body = resp.json()["error"]
    assert body["code"] == "ACCOUNT_BLOCKED"
    assert body["details"]["retry_after"] == 300
    resp = client.post("/api/v1/auth/login", json={"identifier": USERNAME, "password": PASSWORD})
    assert resp.status_code == 423


def test_logout_revokes_session(client, outbox):
    token = verified_login(client, outbox)
    resp = client.post("/api/v1/auth/logout", headers=auth_headers(token))
    assert resp.status_code == 204
    resp = client.get("/api/v1/users/me", headers=auth_headers(token))
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "TOKEN_INVALID"


def test_protected_endpoint_requires_auth(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "TOKEN_INVALID"


def test_invalid_access_token(client):
    resp = client.get("/api/v1/users/me", headers=auth_headers("token-falso"))
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "TOKEN_INVALID"


def test_change_password_ok(client, outbox):
    token = verified_login(client, outbox)
    resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    resp = client.post("/api/v1/auth/login", json={"identifier": USERNAME, "password": PASSWORD})
    assert resp.status_code == 401
    resp = client.post("/api/v1/auth/login", json={"identifier": USERNAME, "password": NEW_PASSWORD})
    assert resp.status_code == 200


def test_change_password_wrong_current(client, outbox):
    token = verified_login(client, outbox)
    resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "incorrecta", "new_password": NEW_PASSWORD},
        headers=auth_headers(token),
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_change_password_policy_error(client, outbox):
    token = verified_login(client, outbox)
    resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": PASSWORD, "new_password": "abc12345"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "PASSWORD_POLICY"


def test_reset_password_flow(client, outbox):
    verified_login(client, outbox)
    resp = client.post("/api/v1/auth/forgot-password", json={"email": EMAIL})
    assert resp.status_code == 200
    reset_token = extract_token(outbox[-1][2])
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": NEW_PASSWORD},
    )
    assert resp.status_code == 200
    resp = client.post("/api/v1/auth/login", json={"identifier": EMAIL, "password": NEW_PASSWORD})
    assert resp.status_code == 200


def test_reset_password_invalid_token(client, outbox):
    client.post("/api/v1/auth/forgot-password", json={"email": EMAIL})
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "token-invalido", "new_password": NEW_PASSWORD},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "TOKEN_INVALID"


def test_verify_email_invalid_token(client, outbox):
    resp = client.post("/api/v1/auth/verify-email", json={"token": "token-invalido"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "TOKEN_INVALID"