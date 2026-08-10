from fastapi.testclient import TestClient

from tests.test_auth import EMAIL, USERNAME, auth_headers, verified_login


def test_me_returns_profile(client: TestClient, outbox):
    token = verified_login(client, outbox)
    resp = client.get("/api/v1/users/me", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["username"] == USERNAME


def test_update_username(client: TestClient, outbox):
    token = verified_login(client, outbox)
    resp = client.patch(
        "/api/v1/users/me",
        json={"username": "nuevo_nombre"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "nuevo_nombre"
    assert data["profile_image_url"] == "/avatars/n.svg"


def test_update_username_taken(client: TestClient, outbox):
    verified_login(client, outbox)
    token = verified_login(client, outbox, username="otro", email="otro@example.com")
    resp = client.patch(
        "/api/v1/users/me",
        json={"username": USERNAME},
        headers=auth_headers(token),
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "USERNAME_TAKEN"


def test_update_email_sets_unverified(client: TestClient, outbox):
    token = verified_login(client, outbox)
    resp = client.patch(
        "/api/v1/users/me",
        json={"email": "nuevo@example.com"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "nuevo@example.com"
    assert data["verified"] is False
    assert len(outbox) == 1
    assert outbox[0][0] == "nuevo@example.com"


def test_update_email_taken(client: TestClient, outbox):
    verified_login(client, outbox)
    token = verified_login(client, outbox, username="otro", email="otro@example.com")
    resp = client.patch(
        "/api/v1/users/me",
        json={"email": EMAIL},
        headers=auth_headers(token),
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "EMAIL_TAKEN"


def test_list_modalities_requires_auth(client: TestClient):
    resp = client.get("/api/v1/modalities")
    assert resp.status_code == 401


def test_list_modalities(client: TestClient, outbox):
    token = verified_login(client, outbox)
    resp = client.get("/api/v1/modalities", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["items"][0]["name"] == "Es un 10 pero..."
    assert data["items"][0]["template"] == "Es un 10 pero ..."