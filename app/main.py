"""Punto de entrada de la API del juego "Es un 10 pero…"."""

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.errors import (
    ApiError,
    api_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.api.routers import auth, matches, modalities, rooms, turns, users
from app.core.config import Settings, get_settings
from app.email.provider import ConsoleEmailProvider
from app.services.auth_service import AuthService
from app.services.match_service import MatchService
from app.services.room_service import RoomService
from app.services.turn_service import TurnService
from app.services.users_service import UsersService
from app.stores.memory import (
    MemoryMatchStore,
    MemoryRoomStore,
    MemorySessionStore,
    MemoryTurnStore,
    MemoryUserStore,
    MemoryVerificationStore,
)


def create_app(
    settings: Settings | None = None,
    outbox: list[tuple[str, str, str]] | None = None,
) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Videojuego multijugador por turnos — API REST",
        version=settings.app_version,
    )

    user_store = MemoryUserStore()
    session_store = MemorySessionStore()
    verification_store = MemoryVerificationStore()
    room_store = MemoryRoomStore()
    match_store = MemoryMatchStore()
    email_provider = ConsoleEmailProvider(outbox)

    auth_service = AuthService(
        settings=settings,
        users=user_store,
        sessions=session_store,
        verifications=verification_store,
        emails=email_provider,
    )
    users_service = UsersService(users=user_store, auth_service=auth_service)
    match_service = MatchService(matches=match_store, rooms=room_store)
    turn_service = TurnService(
        settings=settings, matches=match_service, turns=MemoryTurnStore()
    )
    rooms_service = RoomService(
        settings=settings, rooms=room_store, matches=match_service, turns=turn_service
    )

    app.state.auth_service = auth_service
    app.state.users_service = users_service
    app.state.rooms_service = rooms_service
    app.state.matches_service = match_service
    app.state.turns_service = turn_service
    app.state.email_provider = email_provider

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    if not settings.debug:
        app.add_exception_handler(Exception, unhandled_error_handler)

    api = APIRouter(prefix="/api/v1")
    api.include_router(auth.router)
    api.include_router(users.router)
    api.include_router(modalities.router)
    api.include_router(rooms.router)
    api.include_router(matches.router)
    api.include_router(turns.router)
    app.include_router(api)

    @app.get("/")
    def root() -> dict:
        """Información básica de la API."""
        return {"name": settings.app_name, "version": settings.app_version}

    @app.get("/health")
    def health() -> dict:
        """Health check para monitorear que el servidor está operativo."""
        return {"status": "ok"}

    return app


app = create_app()