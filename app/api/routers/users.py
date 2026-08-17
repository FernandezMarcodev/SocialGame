"""Routers del módulo de usuarios (Apéndice B.2.2)."""

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile

from app.api.deps import get_current_user, get_event_bus, get_rooms_service, get_users_service
from app.api.schemas import GhostDisconnectOut, UpdateProfileIn, UserOut
from app.services.room_service import RoomService
from app.services.realtime_service import EventBus
from app.services.users_service import UsersService
from app.api.errors import ApiError
from app.services.auth_service import AuthService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(user=Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UpdateProfileIn,
    user=Depends(get_current_user),
    users: UsersService = Depends(get_users_service),
) -> UserOut:
    return users.update_profile(user, payload.username, payload.email)


@router.put("/me/avatar", response_model=UserOut)
async def update_avatar(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    users: UsersService = Depends(get_users_service),
) -> UserOut:
    content = await file.read()
    return users.update_avatar(user, content, file.content_type)


async def _get_user_from_token(
    token: str | None = Query(default=None),
    auth_service: AuthService = Depends(lambda r: r.app.state.auth_service),
) -> UserOut:
    """Obtiene usuario desde query param token (para <img src>)."""
    if token:
        try:
            return auth_service.resolve_access_token(token)
        except ApiError:
            pass
    # Si no hay token válido en query, devolvemos 401
    from fastapi import HTTPException
    raise HTTPException(status_code=401, detail="Token inválido")


@router.get("/me/avatar/image")
async def get_avatar_image(
    user=Depends(_get_user_from_token),
) -> Response:
    """Sirve la imagen de avatar desde la base de datos (avatar_storage=database).

    Acepta token en query param `token` para <img src="">.
    """
    if not user.avatar_data or not user.avatar_content_type:
        return Response(status_code=404)
    return Response(content=user.avatar_data, media_type=user.avatar_content_type)


@router.post("/me/rooms/force-leave", response_model=GhostDisconnectOut)
async def force_disconnect(
    user=Depends(get_current_user),
    rooms: RoomService = Depends(get_rooms_service),
    bus: EventBus = Depends(get_event_bus),
) -> GhostDisconnectOut:
    """Desconectar al usuario de todas las salas fantasmas (RF-COM-010).

    Busca la sala en la que el jugador esté registrado (aunque haya dejado
    de estar conectado) y lo elimina, notificando a los jugadores restantes
    vía WebSocket. Si la sala queda vacía se elimina automáticamente.
    """
    room = rooms.force_disconnect(user)
    if room is not None:
        out = rooms.serialize(room)
        await bus.publish("room.updated", {"code": room.code, "room": out.model_dump()})
        return GhostDisconnectOut(
            disconnected=True,
            room_code=room.code,
            message="Te has desconectado de la sala.",
        )
    return GhostDisconnectOut(
        disconnected=False,
        room_code=None,
        message="No estabas en ninguna sala.",
    )