"""Módulo de Comunicación en Tiempo Real (RF-COM-001 a 010).

Implementa el AD-004: gateway WebSocket + bus de eventos asyncio en proceso.
Los routers publican eventos de dominio en el ``EventBus`` y ``RealtimeService``
los convierte en mensajes WS a los jugadores conectados (Apéndice B.2 del DDD).

Incluye soporte para Redis Pub/Sub para escalado horizontal multi-instancia
y mecanismo de heartbeat (ping/pong) para mantener conexiones vivas a través
de NATs, firewalls y balanceadores de carga en Internet.
"""

import asyncio
import inspect
import json
import logging
from typing import Callable, Optional

from fastapi import WebSocket

from app.domain.entities import Match, Room
from app.stores.base import MatchStore, RoomStore

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 25
HEARTBEAT_TIMEOUT = 60

class ConnectionManager:
    """Administra las conexiones WebSocket autenticadas por usuario (RF-COM-002).

    Soporta Redis para escalado horizontal: las conexiones se registran en Redis
    para que otras instancias sepan a qué usuario pertenece cada conexión.
    """

    def __init__(self, redis_client: Optional[object] = None) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._redis = redis_client
        self._heartbeat_tasks: dict[WebSocket, asyncio.Task] = {}
        self._instance_id = f"api-{id(self)}"

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)

        if self._redis:
            try:
                await self._redis.hset(
                    "ws:connections", f"{user_id}:{self._instance_id}", "1"
                )
                await self._redis.expire("ws:connections", HEARTBEAT_TIMEOUT * 2)
            except Exception as e:
                logger.warning("Error registrando conexión en Redis: %s", e)

        self._start_heartbeat(websocket)

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(user_id)
        if not conns:
            return
        conns.discard(websocket)
        if not conns:
            self._connections.pop(user_id, None)

        self._stop_heartbeat(websocket)

        if self._redis:
            try:
                await self._redis.hdel("ws:connections", f"{user_id}:{self._instance_id}")
            except Exception as e:
                logger.warning("Error eliminando conexión de Redis: %s", e)

    def _start_heartbeat(self, websocket: WebSocket) -> None:
        async def heartbeat():
            try:
                while True:
                    await asyncio.sleep(HEARTBEAT_INTERVAL)
                    try:
                        await websocket.send_json({"type": "ping"})
                    except Exception:
                        break
            except asyncio.CancelledError:
                pass

        task = asyncio.create_task(heartbeat())
        self._heartbeat_tasks[websocket] = task

    def _stop_heartbeat(self, websocket: WebSocket) -> None:
        task = self._heartbeat_tasks.pop(websocket, None)
        if task:
            task.cancel()

    async def send_to_user(self, user_id: str, message: dict) -> None:
        for websocket in list(self._connections.get(user_id, ())):
            try:
                await websocket.send_json(message)
            except Exception:
                self._connections.get(user_id, set()).discard(websocket)
                self._stop_heartbeat(websocket)

    async def send_to_room(self, room: Room, message: dict) -> None:
        for player in room.players:
            await self.send_to_user(player.id, message)

    async def broadcast(self, message: dict) -> None:
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, message)

    def get_connected_users(self) -> list[str]:
        return list(self._connections.keys())


class EventBus:
    """Bus de eventos que desacopla la publicación de su envío (AD-004).

    Soporta Redis Pub/Sub para propagar eventos entre múltiples instancias
    de la API detrás de un balanceador de carga.
    """

    def __init__(self, redis_client: Optional[object] = None) -> None:
        self._subscribers: dict[str, list[Callable[[dict], object]]] = {}
        self._redis = redis_client
        self._pubsub_task: Optional[asyncio.Task] = None
        self._instance_id = f"api-{id(self)}"

    def subscribe(self, event: str, handler: Callable[[dict], object]) -> None:
        self._subscribers.setdefault(event, []).append(handler)

    async def start(self) -> None:
        if self._redis and not self._pubsub_task:
            self._pubsub_task = asyncio.create_task(self._listen_redis())

    async def stop(self) -> None:
        if self._pubsub_task:
            self._pubsub_task.cancel()
            try:
                await self._pubsub_task
            except asyncio.CancelledError:
                pass

    async def _listen_redis(self) -> None:
        try:
            pubsub = self._redis.pubsub()
            await pubsub.subscribe("es10p:events")
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    data = json.loads(message["data"])
                    if data.get("instance") == self._instance_id:
                        continue
                    event = data["event"]
                    payload = data["payload"]
                    await self._dispatch_local(event, payload)
                except Exception as e:
                    logger.warning("Error procesando mensaje Redis: %s", e)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Error en listener Redis Pub/Sub: %s", e)

    async def publish(self, event: str, payload: dict) -> None:
        await self._dispatch_local(event, payload)

        if self._redis:
            try:
                message = json.dumps({
                    "event": event,
                    "payload": payload,
                    "instance": self._instance_id,
                })
                await self._redis.publish("es10p:events", message)
            except Exception as e:
                logger.warning("Error publicando en Redis Pub/Sub: %s", e)

    async def _dispatch_local(self, event: str, payload: dict) -> None:
        for handler in list(self._subscribers.get(event, ())):
            result = handler(payload)
            if inspect.isawaitable(result):
                await result


class RealtimeService:
    """Traduce eventos de dominio a mensajes WebSocket (B.2 del DDD)."""

    def __init__(
        self, bus: EventBus, manager: ConnectionManager, rooms: RoomStore,
        matches: MatchStore | None = None,
    ) -> None:
        self._bus = bus
        self._manager = manager
        self._rooms = rooms
        self._matches = matches
        bus.subscribe("room.updated", self._on_room_updated)
        bus.subscribe("room.cancelled", self._on_room_cancelled)
        bus.subscribe("match.started", self._on_match_started)
        bus.subscribe("turn.expired", self._on_turn_expired)
        bus.subscribe("turn.advanced", self._on_turn_advanced)

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

    async def _on_turn_expired(self, payload: dict) -> None:
        match = self._match_from_event(payload)
        if match is None:
            return
        await self._send_to_match(match, {
                "event": "turn.expired",
                "data": {
                    "match_id": payload["match_id"],
                    "turn_id": payload["turn_id"],
                    "author_id": payload["author_id"],
                    "previous_state": payload["previous_state"],
                    "state": payload["state"],
                },
            })

    async def _on_turn_advanced(self, payload: dict) -> None:
        match = self._match_from_event(payload)
        if match is None:
            return
        await self._send_to_match(match, {
                "event": "turn.advanced",
                "data": {
                    "match_id": payload["match_id"],
                    "next_author_id": payload["next_author_id"],
                    "current_turn_id": payload["current_turn_id"],
                    "phase": payload["phase"],
                },
            })

    def _match_from_event(self, payload: dict) -> Match | Room | None:
        """Resuelve la partida/sala objetivo para eventos de turno."""
        match_id = payload["match_id"]
        if self._matches is not None:
            match = self._matches.get(match_id)
            if match is not None:
                return match
        room_code = payload.get("room_code")
        if room_code is None:
            return None
        return self._rooms.get(room_code)

    async def _send_to_match(self, obj: Match | Room, message: dict) -> None:
        """Envía un mensaje a todos los jugadores de una partida o sala."""
        for player in obj.players:
            await self._manager.send_to_user(player.id, message)
