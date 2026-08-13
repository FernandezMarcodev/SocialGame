"""Módulo de Comunicación en Tiempo Real (RF-COM-001 a 010).

Implementa el AD-004: gateway WebSocket + bus de eventos asyncio en proceso.
Los routers publican eventos de dominio en el ``EventBus`` y ``RealtimeService``
los convierte en mensajes WS a los jugadores conectados (Apéndice B.2 del DDD).
"""

import inspect
from typing import Callable

from fastapi import WebSocket

from app.domain.entities import Room
from app.stores.base import RoomStore

class ConnectionManager:
    """Administra las conexiones WebSocket autenticadas por usuario (RF-COM-002)."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(user_id)
        if not conns:
            return
        conns.discard(websocket)
        if not conns:
            self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: str, message: dict) -> None:
        for websocket in list(self._connections.get(user_id, ())):
            try:
                await websocket.send_json(message)
            except Exception:
                self._connections.get(user_id, set()).discard(websocket)

    async def send_to_room(self, room: Room, message: dict) -> None:
        for player in room.players:
            await self.send_to_user(player.id, message)


class EventBus:
    """Bus de eventos en proceso que desacopla la publicación de su envío (AD-004)."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[dict], object]]] = {}

    def subscribe(self, event: str, handler: Callable[[dict], object]) -> None:
        self._subscribers.setdefault(event, []).append(handler)

    async def publish(self, event: str, payload: dict) -> None:
        for handler in list(self._subscribers.get(event, ())):
            result = handler(payload)
            if inspect.isawaitable(result):
                await result


class RealtimeService:
    """Traduce eventos de dominio a mensajes WebSocket (B.2 del DDD)."""

    def __init__(
        self, bus: EventBus, manager: ConnectionManager, rooms: RoomStore
    ) -> None:
        self._bus = bus
        self._manager = manager
        self._rooms = rooms
        bus.subscribe("room.updated", self._on_room_updated)
        bus.subscribe("room.cancelled", self._on_room_cancelled)
        bus.subscribe("match.started", self._on_match_started)

    async def _on_room_updated(self, payload: dict) -> None:
        room = self._rooms.get(payload["code"])
        if room is None:
            return
        await self._manager.send_to_room(
            room, {"event": "room.updated", "data": payload["room"]}
        )

    async def _on_room_cancelled(self, payload: dict) -> None:
        await self._manager.send_to_room(
            payload["room"], {"event": "room.cancelled", "data": {"code": payload["code"]}}
        )

    async def _on_match_started(self, payload: dict) -> None:
        room = self._rooms.get(payload["room_code"])
        if room is None:
            return
        await self._manager.send_to_room(
            room,
            {
                "event": "match.started",
                "data": {
                    "match_id": payload["match_id"],
                    "order": payload["order"],
                    "first_author": payload["first_author"],
                },
            },
        )
