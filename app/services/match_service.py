"""Servicio de partidas.

Implementa RF-PAR-001 a 007 y las reglas RN-017, RN-021 a 023, según los
contratos del Apéndice B.2.4 del DDD. El estado de las partidas vive en
memoria (AD-003): ``created`` → ``initialized`` → ``in_progress`` → ``finished``.
"""

import secrets
from typing import Callable
from uuid import uuid4

from app.api.errors import ApiError
from app.api.schemas import MatchOut, PlayerOut
from app.core.security import utcnow_ms
from app.domain.entities import Match, PlayerRef, Room
from app.stores.base import MatchStore, RoomStore

_MATCH_ID_PREFIX = "m-"
_MATCH_INITIAL_STATES = {"created", "initialized", "in_progress"}
_TOTAL_ROUNDS = 3  # Toda partida dura exactamente 3 rondas (RN-002).


def _new_match_id() -> str:
    return _MATCH_ID_PREFIX + uuid4().hex[:10]


def _serialize_player(player: PlayerRef) -> PlayerOut:
    return PlayerOut(
        id=player.id,
        username=player.username,
        joined_at=player.joined_at,
        profile_image_url=player.profile_image_url,
    )


class MatchService:
    def __init__(
        self,
        matches: MatchStore,
        rooms: RoomStore,
        now: Callable[[], int] | None = None,
    ) -> None:
        self._matches = matches
        self._rooms = rooms
        self._now = now or utcnow_ms

    def serialize(self, match: Match) -> MatchOut:
        return MatchOut(
            match_id=match.match_id,
            room_code=match.room_code,
            state=match.state,
            players=[_serialize_player(p) for p in match.players],
            turn_order=list(match.turn_order),
            current_turn=match.current_turn,
            scores=dict(match.scores),
            created_at=match.created_at,
            turn_index=match.turn_index,
            total_rounds=_TOTAL_ROUNDS,
        )

    def get_match(self, match_id: str) -> Match:
        match = self._matches.get(match_id)
        if match is None:
            raise ApiError(404, "MATCH_NOT_FOUND", "La partida no existe.")
        return match

    def get_match_by_room(self, room_code: str) -> Match:
        """Devuelve la partida asociada a una sala mediante su código (RF-SAL-005)."""
        match = self._matches.get_by_room(room_code)
        if match is None:
            raise ApiError(404, "MATCH_NOT_FOUND", "La partida no existe.")
        return match

    def update(self, match: Match) -> None:
        """Persiste los cambios de una partida en el store subyacente."""
        self._matches.update(match)

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #

    def create_match(self, room: Room, requester_id: str) -> Match:
        """Crea la partida a partir de una sala válida (RF-PAR-001)."""
        if self._matches.get_by_room(room.code) is not None:
            raise ApiError(409, "MATCH_ALREADY_EXISTS", "La partida ya fue creada.")
        if room.state != "available":
            raise ApiError(409, "ROOM_NOT_AVAILABLE", "La sala no está disponible.")
        if room.creator_id != requester_id:
            raise ApiError(403, "NOT_CREATOR", "Solo el creador puede iniciar la partida.")
        if len(room.players) < room.min_players:
            raise ApiError(
                409,
                "MIN_PLAYERS_NOT_REACHED",
                f"Se necesitan al menos {room.min_players} jugadores.",
            )
        match = Match(
            match_id=_new_match_id(),
            room_code=room.code,
            modality_id=room.modality_id,
            state="created",
            players=list(room.players),
            turn_order=[],
            turn_index=0,
            current_turn=None,
            scores={p.id: 0 for p in room.players},
            created_at=self._now(),
        )
        self._matches.add(match)
        return match

    def initialize_match(self, match: Match) -> Match:
        """Inicializa la partida y genera el orden de participación (RF-PAR-002/003).

        El orden se genera para las ``_TOTAL_ROUNDS`` rondas: cada ronda es una
        permutación independiente de los jugadores, de modo que toda partida
        tiene exactamente 3 rondas (RN-002).
        """
        if match.state != "created":
            raise ApiError(409, "MATCH_WRONG_STATE", "La partida no puede inicializarse.")
        base = [p.id for p in match.players]
        order: list[str] = []
        for _ in range(_TOTAL_ROUNDS):
            round_order = list(base)
            secrets.SystemRandom().shuffle(round_order)
            order.extend(round_order)
        match.turn_order = order
        match.state = "initialized"
        self._matches.update(match)
        return match

    def start_first_turn(self, match: Match) -> Match:
        """Marca la partida como en curso con el primer autor (puente a RF-TUR-001)."""
        if match.state != "initialized":
            raise ApiError(409, "MATCH_WRONG_STATE", "La partida no está inicializada.")
        match.state = "in_progress"
        self._matches.update(match)
        return match

    def advance_round(self, match: Match) -> Match:
        """Avanza al siguiente turno o finaliza la ronda (RF-PAR-005/006)."""
        if match.state not in ("initialized", "in_progress"):
            raise ApiError(409, "MATCH_NOT_ACTIVE", "La partida no está en curso.")
        match.current_turn = None
        match.turn_index += 1
        if match.turn_index >= len(match.turn_order):
            return self._finish(match)
        match.state = "in_progress"
        self._matches.update(match)
        return match

    def finish_round(self, match: Match) -> Match:
        """Fuerza el cierre de la ronda (RF-PAR-006)."""
        if match.state != "in_progress":
            raise ApiError(409, "MATCH_NOT_ACTIVE", "La partida no está en curso.")
        return self._finish(match)

    # ------------------------------------------------------------------ #
    # Resultado
    # ------------------------------------------------------------------ #

    def result(self, match_id: str) -> dict:
        """Determina el resultado final (RF-PAR-007, RN-023)."""
        match = self.get_match(match_id)
        if match.state != "finished":
            raise ApiError(409, "MATCH_NOT_FINISHED", "La partida aún no finalizó.")
        return self._result_of(match)

    # ------------------------------------------------------------------ #

    def _finish(self, match: Match) -> Match:
        match.state = "finished"
        self._rooms.remove(match.room_code)
        self._matches.update(match)
        return match

    @staticmethod
    def _result_of(match: Match) -> dict:
        if not match.scores:
            raise ApiError(409, "MATCH_WITHOUT_SCORES", "No hay puntajes registrados.")
        top = max(match.scores.values())
        leaders = [pid for pid, score in match.scores.items() if score == top]
        return {
            "winner_id": None if len(leaders) > 1 else leaders[0],
            "tied": len(leaders) > 1,
            "scores": dict(sorted(match.scores.items(), key=lambda kv: kv[1], reverse=True)),
        }