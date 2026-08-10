"""Servicio de salas de juego.

Implementa RF-SAL-001 a 008 y las reglas de negocio RN-004, RN-006 a 011,
según los contratos del Apéndice B.2.3 del DDD. El estado de las salas vive en
memoria (AD-003): ``available`` → ``in_match`` | ``cancelled`` → ``deleted``.
"""

import secrets
from typing import Callable
from uuid import uuid4

from app.api.errors import ApiError
from app.api.schemas import ModalityOut, PlayerOut, RoomOut
from app.core.config import Settings
from app.core.security import utcnow_ms
from app.domain.entities import PlayerRef, Room, User
from app.services.catalog import get_modality
from app.stores.base import RoomStore, UserStore

_ROOM_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_MATCH_ID_PREFIX = "m-"


def _new_room_code() -> str:
    return "".join(secrets.choice(_ROOM_ALPHABET) for _ in range(6))


def _new_match_id() -> str:
    return _MATCH_ID_PREFIX + uuid4().hex[:10]


class RoomService:
    def __init__(
        self,
        settings: Settings,
        users: UserStore,
        rooms: RoomStore,
        now: Callable[[], int] | None = None,
    ) -> None:
        self._settings = settings
        self._users = users
        self._rooms = rooms
        self._now = now or utcnow_ms

    @staticmethod
    def _serialize_player(player: PlayerRef) -> PlayerOut:
        return PlayerOut(id=player.id, username=player.username, joined_at=player.joined_at)

    def serialize(self, room: Room) -> RoomOut:
        modality = get_modality(room.modality_id)
        if modality is None:
            modality = ModalityOut(id=room.modality_id, name="Desconocida", template="")
        return RoomOut(
            code=room.code,
            state=room.state,
            creator_id=room.creator_id,
            modality=modality,
            players=[self._serialize_player(p) for p in room.players],
            min_players=room.min_players,
            max_players=room.max_players,
            created_at=room.created_at,
        )

    def get_room(self, code: str) -> Room:
        room = self._rooms.get(code)
        if room is None:
            raise ApiError(404, "ROOM_NOT_FOUND", "La sala no existe.")
        return room

    def create_room(self, user: User, modality_id: int) -> Room:
        if self._rooms.get_room_by_player(user.id) is not None:
            raise ApiError(
                409, "PLAYER_ALREADY_IN_SESSION", "Ya estás participando en una sala."
            )
        if get_modality(modality_id) is None:
            raise ApiError(404, "MODALITY_NOT_FOUND", "La modalidad no existe.")
        code = _new_room_code()
        while self._rooms.get(code) is not None:
            code = _new_room_code()
        room = Room(
            code=code,
            creator_id=user.id,
            modality_id=modality_id,
            state="available",
            players=[PlayerRef(id=user.id, username=user.username, joined_at=self._now())],
            min_players=self._settings.room_min_players,
            max_players=self._settings.room_max_players,
            created_at=self._now(),
        )
        self._rooms.add(room)
        return room

    def join_room(self, user: User, code: str) -> Room:
        room = self.get_room(code)
        if self._rooms.get_room_by_player(user.id) is not None:
            raise ApiError(
                409, "PLAYER_ALREADY_IN_SESSION", "Ya estás participando en una sala."
            )
        if room.state != "available":
            raise ApiError(409, "ROOM_NOT_AVAILABLE", "La sala no admite nuevos jugadores.")
        if len(room.players) >= room.max_players:
            raise ApiError(409, "ROOM_FULL", "La sala está completa.")
        self._rooms.add_player(
            code, PlayerRef(id=user.id, username=user.username, joined_at=self._now())
        )
        return room

    def leave_room(self, user: User, code: str) -> Room:
        room = self.get_room(code)
        if not any(p.id == user.id for p in room.players):
            raise ApiError(409, "NOT_IN_ROOM", "No perteneces a esta sala.")
        if room.state != "available":
            raise ApiError(
                409, "ROOM_NOT_AVAILABLE", "No se puede abandonar: la partida ya inició."
            )
        self._rooms.remove_player(code, user.id)
        if room.creator_id == user.id and room.players:
            self._rooms.set_creator(code, room.players[0].id)
        if not room.players:
            self._rooms.remove(code)
        return room

    def cancel_room(self, user: User, code: str) -> None:
        room = self.get_room(code)
        if room.creator_id != user.id:
            raise ApiError(403, "NOT_CREATOR", "Solo el creador puede cancelar la sala.")
        if room.state != "available":
            raise ApiError(400, "ROOM_IN_MATCH", "La partida ya fue iniciada.")
        self._rooms.remove(code)

    def start_match(self, user: User, code: str) -> dict:
        room = self.get_room(code)
        if room.creator_id != user.id:
            raise ApiError(403, "NOT_CREATOR", "Solo el creador puede iniciar la partida.")
        if room.state != "available":
            if room.state == "in_match":
                raise ApiError(400, "ROOM_IN_MATCH", "La partida ya fue iniciada.")
            raise ApiError(409, "ROOM_NOT_AVAILABLE", "La sala no está disponible.")
        if len(room.players) < room.min_players:
            raise ApiError(
                409,
                "MIN_PLAYERS_NOT_REACHED",
                f"Se necesitan al menos {room.min_players} jugadores.",
            )
        self._rooms.set_state(code, "in_match")
        return {"match_id": _new_match_id()}