import re

from fastapi.testclient import TestClient

from tests.test_auth import auth_headers, verified_login

MODALITY_ID = 1


def make_users(client: TestClient, outbox, amount: int) -> list[str]:
    tokens = []
    for i in range(amount):
        tokens.append(verified_login(client, outbox, f"jug{i}", f"jug{i}@example.com"))
    return tokens


def create_room(client: TestClient, token: str) -> dict:
    resp = client.post(
        "/api/v1/rooms",
        json={"modality_id": MODALITY_ID},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_room(client, outbox):
    tokens = make_users(client, outbox, 1)
    data = create_room(client, tokens[0])
    assert re.fullmatch(r"[0-9A-Z]{6}", data["code"])
    assert data["state"] == "available"
    assert data["modality"]["id"] == MODALITY_ID
    assert data["min_players"] == 2
    assert data["max_players"] == 6
    assert len(data["players"]) == 1
    me = client.get("/api/v1/users/me", headers=auth_headers(tokens[0])).json()
    assert data["creator_id"] == me["id"]
    assert data["players"][0]["id"] == me["id"]


def test_create_room_while_in_another_room(client, outbox):
    tokens = make_users(client, outbox, 1)
    create_room(client, tokens[0])
    # Con auto-limpieza, crear una sala nueva limpia la anterior automáticamente.
    resp = client.post(
        "/api/v1/rooms",
        json={"modality_id": MODALITY_ID},
        headers=auth_headers(tokens[0]),
    )
    assert resp.status_code == 201
    new_room = resp.json()
    assert new_room["code"] is not None


def test_create_room_invalid_modality(client, outbox):
    tokens = make_users(client, outbox, 1)
    resp = client.post(
        "/api/v1/rooms", json={"modality_id": 999}, headers=auth_headers(tokens[0])
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "MODALITY_NOT_FOUND"


def test_get_room(client, outbox):
    tokens = make_users(client, outbox, 1)
    room = create_room(client, tokens[0])
    resp = client.get(f"/api/v1/rooms/{room['code']}", headers=auth_headers(tokens[0]))
    assert resp.status_code == 200
    assert resp.json()["code"] == room["code"]


def test_get_room_not_found(client, outbox):
    tokens = make_users(client, outbox, 1)
    resp = client.get("/api/v1/rooms/ZZZZZZ", headers=auth_headers(tokens[0]))
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "ROOM_NOT_FOUND"


def test_join_room(client, outbox):
    tokens = make_users(client, outbox, 2)
    room = create_room(client, tokens[0])
    resp = client.post(
        f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[1])
    )
    assert resp.status_code == 200
    assert len(resp.json()["players"]) == 2


def test_join_full_room(client, outbox):
    tokens = make_users(client, outbox, 7)
    room = create_room(client, tokens[0])
    for token in tokens[1:6]:
        resp = client.post(
            f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(token)
        )
        assert resp.status_code == 200, resp.text
    resp = client.post(
        f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[6])
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "ROOM_FULL"


def test_join_own_room(client, outbox):
    tokens = make_users(client, outbox, 1)
    room = create_room(client, tokens[0])
    resp = client.post(
        f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[0])
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "PLAYER_ALREADY_IN_SESSION"


def test_join_while_in_another_room(client, outbox):
    tokens = make_users(client, outbox, 3)
    room_a = create_room(client, tokens[0])
    create_room(client, tokens[1])
    resp = client.post(
        f"/api/v1/rooms/{room_a['code']}/join", headers=auth_headers(tokens[1])
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "PLAYER_ALREADY_IN_SESSION"


def test_leave_room(client, outbox):
    tokens = make_users(client, outbox, 2)
    room = create_room(client, tokens[0])
    client.post(f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[1]))
    resp = client.post(
        f"/api/v1/rooms/{room['code']}/leave", headers=auth_headers(tokens[1])
    )
    assert resp.status_code == 200
    assert len(resp.json()["players"]) == 1


def test_leave_last_player_removes_room(client, outbox):
    tokens = make_users(client, outbox, 1)
    room = create_room(client, tokens[0])
    resp = client.post(
        f"/api/v1/rooms/{room['code']}/leave", headers=auth_headers(tokens[0])
    )
    assert resp.status_code == 200
    resp = client.get(f"/api/v1/rooms/{room['code']}", headers=auth_headers(tokens[0]))
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "ROOM_NOT_FOUND"


def test_leave_transfers_creator(client, outbox):
    tokens = make_users(client, outbox, 3)
    room = create_room(client, tokens[0])
    client.post(f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[1]))
    client.post(f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[2]))
    resp = client.post(
        f"/api/v1/rooms/{room['code']}/leave", headers=auth_headers(tokens[0])
    )
    assert resp.status_code == 200
    data = resp.json()
    second = client.get("/api/v1/users/me", headers=auth_headers(tokens[1])).json()
    assert data["creator_id"] == second["id"]
    resp = client.post(
        f"/api/v1/rooms/{room['code']}/start", headers=auth_headers(tokens[1])
    )
    assert resp.status_code == 200


def test_leave_not_in_room(client, outbox):
    tokens = make_users(client, outbox, 2)
    room = create_room(client, tokens[0])
    resp = client.post(
        f"/api/v1/rooms/{room['code']}/leave", headers=auth_headers(tokens[1])
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "NOT_IN_ROOM"


def test_cancel_room(client, outbox):
    tokens = make_users(client, outbox, 1)
    room = create_room(client, tokens[0])
    resp = client.delete(f"/api/v1/rooms/{room['code']}", headers=auth_headers(tokens[0]))
    assert resp.status_code == 204
    resp = client.get(f"/api/v1/rooms/{room['code']}", headers=auth_headers(tokens[0]))
    assert resp.status_code == 404


def test_cancel_room_not_creator(client, outbox):
    tokens = make_users(client, outbox, 2)
    room = create_room(client, tokens[0])
    client.post(f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[1]))
    resp = client.delete(f"/api/v1/rooms/{room['code']}", headers=auth_headers(tokens[1]))
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "NOT_CREATOR"


def test_start_requires_min_players(client, outbox):
    tokens = make_users(client, outbox, 1)
    room = create_room(client, tokens[0])
    resp = client.post(
        f"/api/v1/rooms/{room['code']}/start", headers=auth_headers(tokens[0])
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "MIN_PLAYERS_NOT_REACHED"


def test_start_only_creator(client, outbox):
    tokens = make_users(client, outbox, 2)
    room = create_room(client, tokens[0])
    client.post(f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[1]))
    resp = client.post(
        f"/api/v1/rooms/{room['code']}/start", headers=auth_headers(tokens[1])
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "NOT_CREATOR"


def test_start_ok_and_blocks_new_joins(client, outbox):
    tokens = make_users(client, outbox, 3)
    room = create_room(client, tokens[0])
    client.post(f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[1]))
    resp = client.post(
        f"/api/v1/rooms/{room['code']}/start", headers=auth_headers(tokens[0])
    )
    assert resp.status_code == 200
    assert resp.json()["match_id"].startswith("m-")
    resp = client.get(f"/api/v1/rooms/{room['code']}", headers=auth_headers(tokens[0]))
    assert resp.json()["state"] == "in_match"
    resp = client.post(
        f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[2])
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "ROOM_NOT_AVAILABLE"


def test_start_twice_is_rejected(client, outbox):
    tokens = make_users(client, outbox, 2)
    room = create_room(client, tokens[0])
    client.post(f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[1]))
    client.post(f"/api/v1/rooms/{room['code']}/start", headers=auth_headers(tokens[0]))
    resp = client.post(
        f"/api/v1/rooms/{room['code']}/start", headers=auth_headers(tokens[0])
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "ROOM_IN_MATCH"


def test_cancel_started_room_is_rejected(client, outbox):
    tokens = make_users(client, outbox, 2)
    room = create_room(client, tokens[0])
    client.post(f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[1]))
    client.post(f"/api/v1/rooms/{room['code']}/start", headers=auth_headers(tokens[0]))
    resp = client.delete(f"/api/v1/rooms/{room['code']}", headers=auth_headers(tokens[0]))
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "ROOM_IN_MATCH"


def test_force_disconnect_no_room(client, outbox):
    tokens = make_users(client, outbox, 1)
    resp = client.post("/api/v1/users/me/rooms/force-leave", headers=auth_headers(tokens[0]))
    assert resp.status_code == 200
    data = resp.json()
    assert data["disconnected"] is False
    assert data["room_code"] is None


def test_force_disconnect_removes_ghost_room(client, outbox):
    tokens = make_users(client, outbox, 1)
    room = create_room(client, tokens[0])
    resp = client.post("/api/v1/users/me/rooms/force-leave", headers=auth_headers(tokens[0]))
    assert resp.status_code == 200
    data = resp.json()
    assert data["disconnected"] is True
    assert data["room_code"] == room["code"]
    # La sala debe haber sido eliminada (era el último jugador).
    resp = client.get(f"/api/v1/rooms/{room['code']}", headers=auth_headers(tokens[0]))
    assert resp.status_code == 404


def test_force_disconnect_notifies_remaining_players(client, outbox):
    tokens = make_users(client, outbox, 2)
    room = create_room(client, tokens[0])
    client.post(f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[1]))
    resp = client.post("/api/v1/users/me/rooms/force-leave", headers=auth_headers(tokens[0]))
    assert resp.status_code == 200
    data = resp.json()
    assert data["disconnected"] is True
    assert data["room_code"] == room["code"]
    # La sala sigue viva con el jugador restante.
    resp = client.get(f"/api/v1/rooms/{room['code']}", headers=auth_headers(tokens[1]))
    assert resp.status_code == 200
    assert len(resp.json()["players"]) == 1


def test_force_disconnect_transfers_creator(client, outbox):
    tokens = make_users(client, outbox, 2)
    room = create_room(client, tokens[0])
    client.post(f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[1]))
    resp = client.post("/api/v1/users/me/rooms/force-leave", headers=auth_headers(tokens[0]))
    assert resp.status_code == 200
    data = resp.json()
    assert data["disconnected"] is True
    # El creador debe haber pasado al segundo jugador.
    resp = client.get(f"/api/v1/rooms/{room['code']}", headers=auth_headers(tokens[1]))
    second = client.get("/api/v1/users/me", headers=auth_headers(tokens[1])).json()
    assert resp.json()["creator_id"] == second["id"]


def test_force_disconnect_during_in_match(client, outbox):
    """El desconectado forzado debe permitir salir incluso si la partida inició."""
    tokens = make_users(client, outbox, 2)
    room = create_room(client, tokens[0])
    client.post(f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(tokens[1]))
    client.post(f"/api/v1/rooms/{room['code']}/start", headers=auth_headers(tokens[0]))
    resp = client.post("/api/v1/users/me/rooms/force-leave", headers=auth_headers(tokens[0]))
    assert resp.status_code == 200
    data = resp.json()
    assert data["disconnected"] is True
    # El segundo jugador aún puede ver la sala (en_match) y seguir jugando.
    resp = client.get(f"/api/v1/rooms/{room['code']}", headers=auth_headers(tokens[1]))
    assert resp.status_code == 200
    assert len(resp.json()["players"]) == 1


def test_force_disconnect_enables_new_room(client, outbox):
    """Después del force-leave, el jugador puede crear una sala nueva."""
    tokens = make_users(client, outbox, 1)
    create_room(client, tokens[0])
    # Con auto-limpieza, crear una sala nueva limpia la anterior automáticamente.
    resp = client.post("/api/v1/rooms", json={"modality_id": MODALITY_ID}, headers=auth_headers(tokens[0]))
    assert resp.status_code == 201
    # La sala anterior se limpió automáticamente.
    new_room = resp.json()
    # Force-leave también funciona para limpiar salas fantasma manualmente.
    client.post("/api/v1/users/me/rooms/force-leave", headers=auth_headers(tokens[0]))
    # Ahora se puede crear otra sala.
    resp = client.post("/api/v1/rooms", json={"modality_id": MODALITY_ID}, headers=auth_headers(tokens[0]))
    assert resp.status_code == 201


def test_rooms_endpoints_require_auth(client):
    resp = client.get("/api/v1/rooms/AB12CD")
    assert resp.status_code == 401