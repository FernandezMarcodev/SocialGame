"""Tests del módulo de partidas (RF-PAR-001 a 007)."""

import pytest
from fastapi.testclient import TestClient

from app.api.errors import ApiError
from app.domain.entities import Match, PlayerRef, Room
from app.services.match_service import MatchService
from app.stores.memory import MemoryMatchStore, MemoryRoomStore
from tests.test_auth import auth_headers, verified_login
from tests.test_rooms import MODALITY_ID, create_room


def make_tokens(client, outbox, amount):
    return [
        verified_login(client, outbox, f"jug{i}", f"jug{i}@example.com")
        for i in range(amount)
    ]


def room(players_ids, code="AB12CD", min_players=2):
    return Room(
        code=code,
        creator_id=players_ids[0],
        modality_id=1,
        state="available",
        players=[PlayerRef(id=pid, username=pid, joined_at=1) for pid in players_ids],
        min_players=min_players,
        max_players=6,
        created_at=1,
    )


def make_service(r: Room) -> MatchService:
    service = MatchService(matches=MemoryMatchStore(), rooms=MemoryRoomStore())
    service._rooms.add(r)
    return service


def created_match(r: Room) -> Match:
    service = make_service(r)
    match = service.create_match(r, r.creator_id)
    match = service.initialize_match(match)
    return match


def start_match_http(client, outbox, amount=2):
    tokens = make_tokens(client, outbox, amount)
    room_data = create_room(client, tokens[0])
    for token in tokens[1:]:
        resp = client.post(
            f"/api/v1/rooms/{room_data['code']}/join", headers=auth_headers(token)
        )
        assert resp.status_code == 200, resp.text
    resp = client.post(
        f"/api/v1/rooms/{room_data['code']}/start", headers=auth_headers(tokens[0])
    )
    assert resp.status_code == 200, resp.text
    return tokens, room_data["code"], resp.json()["match_id"]


class TestMatchHttp:
    def test_get_match_after_start(self, client, outbox):
        tokens, room_code, match_id = start_match_http(client, outbox, 2)
        me = client.get("/api/v1/users/me", headers=auth_headers(tokens[0])).json()
        other = client.get("/api/v1/users/me", headers=auth_headers(tokens[1])).json()
        resp = client.get(f"/api/v1/matches/{match_id}", headers=auth_headers(tokens[0]))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["match_id"] == match_id
        assert data["room_code"] == room_code
        assert data["state"] == "in_progress"
        assert len(data["players"]) == 2
        assert len(data["turn_order"]) == 6  # 2 jugadores x 3 rondas
        assert sorted(data["turn_order"]) == sorted([me["id"], other["id"]] * 3)
        assert isinstance(data["current_turn"], str) and data["current_turn"].startswith("t-")
        assert data["scores"] == {me["id"]: 0, other["id"]: 0}

    def test_get_match_not_found(self, client, outbox):
        tokens = make_tokens(client, outbox, 1)
        resp = client.get("/api/v1/matches/m-0000000000", headers=auth_headers(tokens[0]))
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "MATCH_NOT_FOUND"

    def test_get_match_by_room_code(self, client, outbox):
        tokens, room_code, match_id = start_match_http(client, outbox, 2)
        resp = client.get(
            f"/api/v1/matches/by-room/{room_code}", headers=auth_headers(tokens[1])
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["match_id"] == match_id
        assert data["room_code"] == room_code
        assert data["state"] == "in_progress"

    def test_get_match_by_room_not_found(self, client, outbox):
        tokens = make_tokens(client, outbox, 1)
        resp = client.get(
            "/api/v1/matches/by-room/ZZZZZZ", headers=auth_headers(tokens[0])
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "MATCH_NOT_FOUND"

    def test_get_match_by_room_requires_auth(self, client):
        resp = client.get("/api/v1/matches/by-room/ZZZZZZ")
        assert resp.status_code == 401


class TestMatchService:
    def test_create_generates_order(self):
        r = room(["u1", "u2", "u3"])
        service = make_service(r)
        match = service.create_match(r, "u1")
        assert match.state == "created"
        assert match.scores == {"u1": 0, "u2": 0, "u3": 0}
        match = service.initialize_match(match)
        assert match.state == "initialized"
        assert len(match.turn_order) == 9  # 3 jugadores x 3 rondas
        assert sorted(match.turn_order) == sorted(["u1", "u2", "u3"] * 3)

    def test_start_then_advance_then_finish(self):
        r = room(["u1", "u2"])
        service = make_service(r)
        match = service.create_match(r, "u1")
        service.initialize_match(match)
        service.start_first_turn(match)
        assert match.state == "in_progress"
        service.advance_round(match)
        assert match.state == "in_progress"
        assert match.turn_index == 1
        # La partida dura 3 rondas x 2 jugadores = 6 turnos.
        while match.state != "finished":
            match = service.advance_round(match)
        assert match.turn_index == 6

    def test_finish_removes_room(self):
        r = room(["u1", "u2"])
        service = make_service(r)
        match = service.create_match(r, "u1")
        service.initialize_match(match)
        service.start_first_turn(match)
        for _ in range(len(match.turn_order)):
            service.advance_round(match)
        assert service._rooms.get(r.code) is None

    def test_result_winner(self):
        r = room(["u1", "u2"])
        service = make_service(r)
        match = service.create_match(r, "u1")
        service.initialize_match(match)
        match.scores = {"u1": 3, "u2": 1}
        service._finish(match)
        result = service.result(match.match_id)
        assert result == {"winner_id": "u1", "tied": False, "scores": {"u1": 3, "u2": 1}}

    def test_result_tie(self):
        r = room(["u1", "u2", "u3"])
        service = make_service(r)
        match = service.create_match(r, "u1")
        service.initialize_match(match)
        match.scores = {"u1": 2, "u2": 2, "u3": 0}
        service._finish(match)
        result = service.result(match.match_id)
        assert result["winner_id"] is None
        assert result["tied"] is True

    def test_result_requires_finished(self):
        r = room(["u1", "u2"])
        service = make_service(r)
        match = service.create_match(r, "u1")
        service.initialize_match(match)
        service.start_first_turn(match)
        with pytest.raises(ApiError) as exc:
            service.result(match.match_id)
        assert exc.value.code == "MATCH_NOT_FINISHED"

    def test_advance_rejects_unknown_match(self):
        r = room(["u1", "u2"])
        service = make_service(r)
        service.create_match(r, "u1")
        with pytest.raises(ApiError) as exc:
            service.get_match("m-inexistente")
        assert exc.value.code == "MATCH_NOT_FOUND"

    def test_advance_rejects_finished(self):
        r = room(["u1", "u2"])
        service = make_service(r)
        match = service.create_match(r, "u1")
        service.initialize_match(match)
        service.start_first_turn(match)
        for _ in range(len(match.turn_order)):
            service.advance_round(match)
        with pytest.raises(ApiError) as exc:
            service.advance_round(match)
        assert exc.value.code == "MATCH_NOT_ACTIVE"

    def test_create_rejects_non_creator(self):
        r = room(["u1", "u2"])
        service = make_service(r)
        with pytest.raises(ApiError) as exc:
            service.create_match(r, "u2")
        assert exc.value.code == "NOT_CREATOR"

    def test_create_rejects_not_available_room(self):
        r = room(["u1", "u2"])
        r.state = "in_match"
        service = make_service(r)
        with pytest.raises(ApiError) as exc:
            service.create_match(r, "u1")
        assert exc.value.code == "ROOM_NOT_AVAILABLE"

    def test_create_rejects_insufficient_players(self):
        r = room(["u1"])
        service = make_service(r)
        with pytest.raises(ApiError) as exc:
            service.create_match(r, "u1")
        assert exc.value.code == "MIN_PLAYERS_NOT_REACHED"

    def test_duplicate_creation_rejected(self):
        r = room(["u1", "u2"])
        service = make_service(r)
        service.create_match(r, "u1")
        with pytest.raises(ApiError) as exc:
            service.create_match(r, "u1")
        assert exc.value.code == "MATCH_ALREADY_EXISTS"