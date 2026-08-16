"""Gateway WebSocket (RF-COM-001, AD-004). Ruta: /api/v1/ws.

Conexión persistente autenticada por token. El servidor empuja los eventos del
dominio (B.2 del DDD) a los jugadores conectados; los mensajes entrantes del
cliente se consumen para mantener la conexión activa.
"""

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.api.errors import ApiError
from app.services.realtime_service import ConnectionManager

router = APIRouter(tags=["realtime"])
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, token: str = Query(default="")
) -> None:
    state = websocket.scope["app"].state
    auth_service = state.auth_service
    manager: ConnectionManager = state.connection_manager
    try:
        user = auth_service.resolve_access_token(token)
    except ApiError:
        await websocket.close(code=4401)
        return
    logger.info("websocket conectado: %s (id=%s)", user.username, user.id)
    await manager.connect(user.id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except (WebSocketDisconnect, RuntimeError):
        await manager.disconnect(user.id, websocket)
