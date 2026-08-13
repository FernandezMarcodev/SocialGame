import os

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from tests.test_auth import EMAIL, USERNAME, auth_headers, verified_login


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, debug=True, upload_dir=str(tmp_path / "uploads"))


def test_me_returns_profile(client: TestClient, outbox):
    token = verified_login(client, outbox)
    resp = client.get("/api/v1/users/me", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["username"] == USERNAME


def test_update_username(client: TestClient, outbox):
    token = verified_login(client, outbox)
    before = client.get("/api/v1/users/me", headers=auth_headers(token)).json()
    resp = client.patch(
        "/api/v1/users/me",
        json={"username": "nuevo_nombre"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "nuevo_nombre"
    # El avatar no se pierde al cambiar el nombre de usuario.
    assert data["profile_image_url"] == before["profile_image_url"]


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


# ---- Foto de perfil (RF-USR-007) ----------------------------------------------

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def _upload(client, token, filename, content, content_type):
    return client.put(
        "/api/v1/users/me/avatar",
        files={"file": (filename, content, content_type)},
        headers=auth_headers(token),
    )


def test_upload_avatar(client: TestClient, outbox):
    token = verified_login(client, outbox)
    resp = _upload(client, token, "foto.png", PNG, "image/png")
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile_image_url"].startswith("/uploads/")
    upload_dir = client.app.state.users_service._upload_dir
    files = os.listdir(upload_dir)
    assert len(files) == 1
    with open(os.path.join(upload_dir, files[0]), "rb") as f:
        assert f.read() == PNG


def test_upload_avatar_replaces_previous(client: TestClient, outbox):
    token = verified_login(client, outbox)
    assert _upload(client, token, "a.png", PNG, "image/png").status_code == 200
    resp = _upload(client, token, "b.jpg", b"\xff\xd8jpeg", "image/jpeg")
    assert resp.status_code == 200
    assert resp.json()["profile_image_url"].endswith(".jpg")
    assert len(os.listdir(client.app.state.users_service._upload_dir)) == 1


def test_upload_avatar_rejects_unsupported_type(client: TestClient, outbox):
    token = verified_login(client, outbox)
    resp = _upload(client, token, "x.txt", b"hola", "text/plain")
    assert resp.status_code == 415
    assert resp.json()["error"]["code"] == "UNSUPPORTED_IMAGE_TYPE"


def test_upload_avatar_rejects_too_large(client: TestClient, outbox):
    token = verified_login(client, outbox)
    resp = _upload(client, token, "big.png", b"x" * (2_000_001), "image/png")
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "IMAGE_TOO_LARGE"