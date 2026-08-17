"""Servicio de salas de juego.

Implementa RF-SAL-001 a 008 y las reglas de negocio RN-004, RN-006 a 011,
según los contratos del Apéndice B.2.3 del DDD. El estado de las salas vive en
memoria (AD-003): ``available`` → ``in_match`` | ``cancelled`` → ``deleted``.
"""

import secrets
from typing import Callable

from app.api.errors import ApiError
from app.api.schemas import ModalityOut, PlayerOut, RoomOut
from app.core.config import Settings
from app.core.security import utcnow_ms
from app.domain.entities import PlayerRef, Room, User
from app.services.catalog import get_modality
from app.services.match_service import MatchService
from app.services.turn_service import TurnService
from app.stores.base import RoomStore

_ROOM_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _new_room_code() -> str:
    return "".join(secrets.choice(_ROOM_ALPHABET) for _ in range(6))


class RoomService:
    def __init__(
        self,
        settings: Settings,
        rooms: RoomStore,
        matches: MatchService,
        turns: TurnService,
        now: Callable[[], int] | None = None,
    ) -> None:
        self._settings = settings
        self._rooms = rooms
        self._matches = matches
        self._turns = turns
        self._now = now or utcnow_ms

    def _player_ref(self, user: User) -> PlayerRef:
        return PlayerRef(
            id=user.id,
            username=user.username,
            joined_at=self._now(),
            profile_image_url=user.profile_image_url,
        )

    @staticmethod
    def _serialize_player(player: PlayerRef) -> PlayerOut:
        return PlayerOut(
            id=player.id,
            username=player.username,
            joined_at=player.joined_at,
            profile_image_url=player.profile_image_url,
        )

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
            players=[self._player_ref(user)],
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
        updated = self._rooms.add_player(code, self._player_ref(user))
        return updated if updated is not None else room

    def leave_room(self, user: User, code: str) -> Room:
        room = self.get_room(code)
        if not any(p.id == user.id for p in room.players):
            raise ApiError(409, "NOT_IN_ROOM", "No perteneces a esta sala.")
        if room.state != "available":
            raise ApiError(
                409, "ROOM_NOT_AVAILABLE", "No se puede abandonar: la partida ya inició."
            )
        room = self._rooms.remove_player(code, user.id)
        if room is None:
            return room
        if room.creator_id == user.id and room.players:
            room = self._rooms.set_creator(code, room.players[0].id)
        if room is not None and not room.players:
            self._rooms.remove(code)
        return room

    def force_disconnect(self, user: User) -> Room | None:
        """Desconecta al jugador de su sala actual, incluso si la partida inició.

        Resuelve el problema de salas fantasma (RF-COM-010): cuando un jugador
        se desconecta sin abandonar explícitamente, queda bloqueado en la sala
        y no puede crear ni unirse a otra (RN-004). Este método busca la sala
        del jugador por su *user_id* y lo elimina, transfiriendo la creación
        si es necesario y borrando la sala cuando queda vacía.

        Devuelve la sala si quedan jugadores (para notificarlos vía WS),
        o ``None`` si el jugador no estaba en ninguna sala o la sala fue
        eliminada por quedar vacía.
        """
        room = self._rooms.get_room_by_player(user.id)
        if room is None:
            return None
        room = self._rooms.remove_player(room.code, user.id)
        if room is None:
            return None
        if room.creator_id == user.id and room.players:
            room = self._rooms.set_creator(room.code, room.players[0].id)
        if room is not None and not room.players:
            self._rooms.remove(room.code)
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
        match = self._matches.create_match(room, user.id)
        self._matches.initialize_match(match)
        self._turns.start_match(match)
        self._rooms.set_state(code, "in_match")
        return {"match_id": match.match_id}