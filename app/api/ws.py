"""Gateway WebSocket (RF-COM-001, AD-004). Ruta: /api/v1/ws.

Conexión persistente autenticada por token. El servidor empuja los eventos del
dominio (B.2 del DDD) a los jugadores conectados; los mensajes entrantes del
cliente se consumen para mantener la conexión activa.

Incluye soporte para heartbeat (ping/pong) para detectar conexiones muertas
a través de NATs, firewalls y balanceadores de carga en Internet.
"""

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.api.errors import ApiError
from app.services.realtime_service import ConnectionManager, EventBus
from app.services.room_service import RoomService

router = APIRouter(tags=["realtime"])
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, token: str = Query(default="")
) -> None:
    state = websocket.scope["app"].state
    auth_service = state.auth_service
    manager: ConnectionManager = state.connection_manager
    rooms: RoomService = state.rooms_service
    bus: EventBus = state.event_bus
    try:
        user = auth_service.resolve_access_token(token)
    except ApiError:
        await websocket.close(code=4401)
        return
    logger.info("websocket conectado: %s (id=%s)", user.username, user.id)
    await manager.connect(user.id, websocket)
    try:
        while True:
            message = await websocket.receive_text()
            await _handle_client_message(websocket, message)
    except (WebSocketDisconnect, RuntimeError):
        await manager.disconnect(user.id, websocket)
        await _on_player_disconnected(user, rooms, bus, manager)


async def _handle_client_message(websocket: WebSocket, message: str) -> None:
    """Procesa mensajes entrantes del cliente (pong, etc.)."""
    try:
        data = json.loads(message)
    except Exception:
        return

    if data.get("type") == "pong":
        pass


async def _on_player_disconnected(
    user, rooms: RoomService, bus: EventBus, manager: ConnectionManager
) -> None:
    """Limpieza automática de salas fantasma (RF-COM-010).

    Cuando un jugador se desconecta del WebSocket sin abandonar la sala
    explícitamente, se elimina de su sala actual. Si la sala queda vacía
    se borra; si quedan jugadores se les notifica vía WebSocket.

    SOLO limpia si el usuario no tiene OTRA conexión WebSocket activa.
    """
    try:
        # Verificar si el usuario tiene otras conexiones WebSocket activas
        other_connections = manager.get_user_connections(user.id)
        if other_connections:
            logger.debug(
                "usuario %s tiene %d conexiones WS activas, no limpio sala fantasma",
                user.username, len(other_connections)
            )
            return

        room = rooms.force_disconnect(user)
        if room is not None:
            out = rooms.serialize(room)
            await bus.publish(
                "room.updated", {"code": room.code, "room": out.model_dump()}
            )
            logger.info(
                "sala fantasma limpiada: %s dejó la sala %s",
                user.username,
                room.code,
            )
    except Exception:
        logger.exception(
            "error limpiando sala fantasma para %s", user.username
        )


import json
