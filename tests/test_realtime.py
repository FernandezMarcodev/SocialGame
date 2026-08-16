"""Tests del módulo de Comunicación en Tiempo Real (RF-COM, AD-004, B.2)."""

import asyncio

import pytest
from starlette.websockets import WebSocketDisconnect

from app.domain.entities import PlayerRef, Room
from app.services.realtime_service import ConnectionManager, EventBus, RealtimeService
from tests.test_auth import auth_headers, verified_login


def run(coro):
    return asyncio.run(coro)


class FakeWebSocket:
    def __init__(self):
        self.sent = []

    async def accept(self):
        pass

    async def send_json(self, message):
        self.sent.append(message)


def make_room(code="AB12CD", state="available", players=("u1",)):
    return Room(
        code=code,
        creator_id=players[0],
        modality_id=1,
        state=state,
        players=[PlayerRef(id=p, username=p, joined_at=1) for p in players],
        min_players=2,
        max_players=6,
        created_at=1,
    )


class TestConnectionManager:
    def test_connect_and_send_to_user(self):
        manager = ConnectionManager()
        ws = FakeWebSocket()

        async def scenario():
            await manager.connect("u1", ws)
            await manager.send_to_user("u1", {"event": "x"})

        run(scenario())
        assert ws.sent == [{"event": "x"}]

    def test_send_to_room_routes_to_players(self):
        manager = ConnectionManager()
        wsa, wsb = FakeWebSocket(), FakeWebSocket()
        room = make_room(state="available", players=("u1", "u2"))

        async def scenario():
            await manager.connect("u1", wsa)
            await manager.connect("u2", wsb)
            await manager.send_to_room(room, {"event": "match.started"})

        run(scenario())
        assert wsa.sent == [{"event": "match.started"}]
        assert wsb.sent == [{"event": "match.started"}]

    def test_disconnect_removes_connection(self):
        manager = ConnectionManager()
        ws = FakeWebSocket()

        async def scenario():
            await manager.connect("u1", ws)
            await manager.disconnect("u1", ws)
            await manager.send_to_user("u1", {"event": "x"})

        run(scenario())
        assert ws.sent == []


class TestEventBus:
    def test_publish_calls_subscribers(self):
        bus = EventBus()
        captured = []
        bus.subscribe("match.started", lambda p: captured.append(p))

        async def scenario():
            await bus.publish("match.started", {"match_id": "m-1"})
            await bus.publish("other", {"match_id": "m-2"})

        run(scenario())
        assert captured == [{"match_id": "m-1"}]


class FakeRoomStore:
    def __init__(self):
        self.rooms = {}

    def add(self, room):
        self.rooms[room.code] = room

    def get(self, code):
        return self.rooms.get(code)


class TestRealtimeService:
    def _make(self):
        bus = EventBus()
        manager = ConnectionManager()
        store = FakeRoomStore()
        service = RealtimeService(bus=bus, manager=manager, rooms=store)
        return bus, manager, service, store

    def test_match_started_event_shape_b2(self):
        bus, manager, service, store = self._make()
        store.add(make_room(state="in_match", players=("u1", "u2")))
        wsa, wsb = FakeWebSocket(), FakeWebSocket()

        async def scenario():
            await manager.connect("u1", wsa)
            await manager.connect("u2", wsb)
            await bus.publish(
                "match.started",
                {"match_id": "m-1", "room_code": "AB12CD", "order": ["u1", "u2"], "first_author": "u1"},
            )

        run(scenario())
        expected = {"event": "match.started", "data": {"match_id": "m-1", "order": ["u1", "u2"], "first_author": "u1"}}
        assert wsa.sent == [expected]
        assert wsb.sent == [expected]

    def test_room_cancelled_notifies_players(self):
        bus, manager, service, store = self._make()
        room = make_room(players=("u1",))
        ws = FakeWebSocket()

        async def scenario():
            await manager.connect("u1", ws)
            await bus.publish("room.cancelled", {"code": "AB12CD", "room": room})

        run(scenario())
        assert ws.sent == [{"event": "room.cancelled", "data": {"code": "AB12CD"}}]


class TestRealtimeHttp:
    def test_start_match_publishes_match_started(self, client, outbox):
        token_a = verified_login(client, outbox, "rt_a", "rt_a@example.com")
        token_b = verified_login(client, outbox, "rt_b", "rt_b@example.com")
        room = client.post(
            "/api/v1/rooms", headers=auth_headers(token_a), json={"modality_id": 1}
        ).json()
        client.post(f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(token_b))

        event_bus = client.app.state.event_bus
        captured = []
        event_bus.subscribe("match.started", lambda p: captured.append(p))

        resp = client.post(
            f"/api/v1/rooms/{room['code']}/start", headers=auth_headers(token_a)
        )
        assert resp.status_code == 200, resp.text
        match_id = resp.json()["match_id"]
        assert captured, "el inicio de partida debe publicar match.started"
        payload = captured[0]
        assert payload["match_id"] == match_id
        assert payload["room_code"] == room["code"]
        assert len(payload["order"]) == 3 * 2
        assert payload["first_author"] in payload["order"]

    def test_join_publishes_room_updated(self, client, outbox):
        token_a = verified_login(client, outbox, "rt_c", "rt_c@example.com")
        token_b = verified_login(client, outbox, "rt_d", "rt_d@example.com")
        room = client.post(
            "/api/v1/rooms", headers=auth_headers(token_a), json={"modality_id": 1}
        ).json()

        event_bus = client.app.state.event_bus
        captured = []
        event_bus.subscribe("room.updated", lambda p: captured.append(p))

        resp = client.post(
            f"/api/v1/rooms/{room['code']}/join", headers=auth_headers(token_b)
        )
        assert resp.status_code == 200, resp.text
        assert captured, "la unión a la sala debe publicar room.updated"
        payload = captured[0]
        assert payload["code"] == room["code"]
        assert len(payload["room"]["players"]) == 2


class TestWebSocketGateway:
    def test_gateway_accepts_valid_token(self, client, outbox):
        token = verified_login(client, outbox, "ws_user", "ws_user@example.com")
        with client.websocket_connect(f"/api/v1/ws?token={token}"):
            pass

    def test_gateway_rejects_invalid_token(self, client):
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/api/v1/ws?token=invalido"):
                pass
