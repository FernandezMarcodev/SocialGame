"""Punto de entrada de la API del juego "Es un 10 pero…"."""

import os

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from app.api.errors import (
    ApiError,
    api_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.api.routers import auth, matches, modalities, rooms, scoring, turns, users
from app.api.ws import router as realtime_router
from app.core.config import Settings, get_settings
from app.email.provider import ConsoleEmailProvider, SmtpEmailProvider
from app.services.auth_service import AuthService
from app.services.match_service import MatchService
from app.services.realtime_service import ConnectionManager, EventBus, RealtimeService
from app.services.room_service import RoomService
from app.services.scoring_service import ScoringService
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

    if settings.database_url:
        from app.stores.database import (
            Database,
            DatabaseMatchStore,
            DatabaseRoomStore,
            DatabaseSessionStore,
            DatabaseTurnStore,
            DatabaseUserStore,
            DatabaseVerificationStore,
        )

        db = Database(settings.database_url)
        user_store = DatabaseUserStore(db)
        session_store = DatabaseSessionStore(db)
        verification_store = DatabaseVerificationStore(db)
        room_store = DatabaseRoomStore(db)
        match_store = DatabaseMatchStore(db)
        turn_store = DatabaseTurnStore(db)
        if settings.email_provider == "smtp" and settings.smtp_host:
            email_provider = SmtpEmailProvider(
                host=settings.smtp_host,
                port=settings.smtp_port,
                user=settings.smtp_user,
                password=settings.smtp_password,
                frm=settings.smtp_from,
                use_tls=settings.smtp_use_tls,
            )
        else:
            email_provider = ConsoleEmailProvider(outbox)
    else:
        user_store = MemoryUserStore()
        session_store = MemorySessionStore()
        verification_store = MemoryVerificationStore()
        room_store = MemoryRoomStore()
        match_store = MemoryMatchStore()
        turn_store = MemoryTurnStore()
        email_provider = ConsoleEmailProvider(outbox)

    event_bus = EventBus()
    connection_manager = ConnectionManager()
    realtime_service = RealtimeService(
        bus=event_bus, manager=connection_manager, rooms=room_store
    )

    auth_service = AuthService(
        settings=settings,
        users=user_store,
        sessions=session_store,
        verifications=verification_store,
        emails=email_provider,
    )
    users_service = UsersService(
        users=user_store,
        auth_service=auth_service,
        upload_dir=settings.upload_dir,
        max_avatar_bytes=settings.max_avatar_bytes,
    )
    match_service = MatchService(matches=match_store, rooms=room_store)
    scoring_service = ScoringService(matches=match_service)
    turn_service = TurnService(
        settings=settings,
        matches=match_service,
        turns=turn_store,
        scoring=scoring_service,
    )
    rooms_service = RoomService(
        settings=settings, rooms=room_store, matches=match_service, turns=turn_service
    )

    app.state.auth_service = auth_service
    app.state.users_service = users_service
    app.state.rooms_service = rooms_service
    app.state.matches_service = match_service
    app.state.turns_service = turn_service
    app.state.scoring_service = scoring_service
    app.state.email_provider = email_provider
    app.state.event_bus = event_bus
    app.state.connection_manager = connection_manager
    app.state.realtime_service = realtime_service

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    if not settings.debug:
        app.add_exception_handler(Exception, unhandled_error_handler)

    # Avatares subidos por los usuarios (RF-USR-007).
    os.makedirs(settings.upload_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

    api = APIRouter(prefix="/api/v1")
    api.include_router(auth.router)
    api.include_router(users.router)
    api.include_router(modalities.router)
    api.include_router(rooms.router)
    api.include_router(matches.router)
    api.include_router(turns.router)
    api.include_router(scoring.router)
    api.include_router(realtime_router)
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