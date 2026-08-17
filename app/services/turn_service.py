"""Servicio de turnos.

Implementa RF-TUR-001 a 011 y las reglas RN-012 a 017, 020, según los
contratos del Apéndice B.2.5 del DDD. El estado de cada turno vive en memoria
(AD-003): ``active`` → ``voting`` → ``finished`` | ``discarded``.

Los vencimientos (RF-TUR-005/008) se evalúan de forma diferida: al consultar la
partida o al intentar actuar se cierra el turno vencido antes de continuar.
"""

from typing import Callable
from uuid import uuid4

from app.api.errors import ApiError
from app.api.schemas import TurnOut, VoteOut
from app.core.config import Settings
from app.core.security import utcnow_ms
from app.domain.entities import Match, Turn, Vote
from app.services.match_service import MatchService
from app.services.realtime_service import EventBus
from app.services.scoring_service import ScoringService
from app.stores.base import TurnStore

_TURN_ID_PREFIX = "t-"


def _new_turn_id() -> str:
    return _TURN_ID_PREFIX + uuid4().hex[:10]


class TurnService:
    def __init__(
        self,
        settings: Settings,
        matches: MatchService,
        turns: TurnStore,
        scoring: ScoringService,
        bus: EventBus | None = None,
        now: Callable[[], int] | None = None,
    ) -> None:
        self._settings = settings
        self._matches = matches
        self._turns = turns
        self._scoring = scoring
        self._bus = bus
        self._now = now or utcnow_ms

    # ------------------------------------------------------------------ #
    # Lectura
    # ------------------------------------------------------------------ #

    def get_turn(self, turn_id: str) -> Turn:
        turn = self._turns.get(turn_id)
        if turn is None:
            raise ApiError(404, "TURN_NOT_FOUND", "El turno no existe.")
        return turn

    def current_turn(self, match_id: str) -> Turn | None:
        match = self._matches.get_match(match_id)
        if match.current_turn is None:
            return None
        return self.get_turn(match.current_turn)

    def serialize_turn(self, turn: Turn) -> TurnOut:
        resolved = turn.state in ("finished", "discarded")
        published = turn.state in ("voting", "finished", "discarded")
        return TurnOut(
            turn_id=turn.turn_id,
            match_id=turn.match_id,
            author_id=turn.author_id,
            state=turn.state,
            phrase=turn.phrase if published else None,
            secret_score=turn.secret_score if resolved else None,
            created_at=turn.created_at,
            expires_at=turn.expires_at,
            voting_ends_at=turn.voting_ends_at,
            votes=[VoteOut(voter_id=v.voter_id, value=v.value) for v in turn.votes]
            if resolved
            else [],
            votes_count=len(turn.votes),
            points=turn.points,
        )

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #

    def start_match(self, match: Match) -> Turn:
        """Crea el primer turno de la partida (RF-TUR-001, RF-PAR-002)."""
        self._matches.start_first_turn(match)
        return self._create_turn(match)

    async def settle_expired(self, match_id: str) -> Match:
        """Cierra turnos vencidos de forma diferida (RF-TUR-005/008).

        Si un turno se expiró (fase de autor o votación), se finaliza y avanza
        al siguiente, publicando eventos de tiempo real para notificar a los
        jugadores (RF-COM-011). Esto evita que los clientes queden bloqueados
        con un turno vencido sin saberlo.
        """
        match = self._matches.get_match(match_id)
        if match.state != "in_progress" or match.current_turn is None:
            return match
        turn = self.get_turn(match.current_turn)
        now = self._now()
        closed = False
        if turn.state == "active" and now > turn.expires_at:
            await self._close_and_advance(match, turn, expired_from="active")
            closed = True
        elif turn.state == "voting" and now > turn.voting_ends_at:
            await self._close_and_advance(match, turn, expired_from="voting")
            closed = True
        return self._matches.get_match(match_id)

    async def _close_and_advance(self, match: Match, turn: Turn, expired_from: str) -> None:
        """Cierra un turno vencido (discard/finalize + advance) y notifica a la sala."""
        previous_state = turn.state
        if previous_state == "active":
            self._discard(turn)
        else:
            self._finalize(turn, match)
        self._turns.update(turn)
        self._matches.update(match)
        await self._notify_turn_closed(match, turn, previous_state)
        self._advance(match)
        await self._notify_turn_advanced(match, turn)

    async def _notify_turn_closed(self, match: Match, turn: Turn, turn_was: str) -> None:
        """Notifica a la sala que un turno venció sin acción del jugador."""
        if self._bus is None:
            return
        await self._bus.publish(
            "turn.expired",
            {
                "match_id": match.match_id,
                "turn_id": turn.turn_id,
                "previous_state": turn_was,
                "state": turn.state,
                "author_id": turn.author_id,
            },
        )

    async def _notify_turn_advanced(self, match: Match, turn: Turn) -> None:
        """Notifica a la sala que el turno avanzó al siguiente autor."""
        if self._bus is None:
            return
        await self._bus.publish(
            "turn.advanced",
            {
                "match_id": match.match_id,
                "previous_turn_id": turn.turn_id,
                "current_turn_id": match.current_turn,
                "next_author_id": match.turn_order[match.turn_index]
                if match.turn_index < len(match.turn_order)
                else None,
                "phase": "voting" if turn.state == "voting" else "authoring",
            },
        )

    # ------------------------------------------------------------------ #
    # Acciones del autor y votantes
    # ------------------------------------------------------------------ #

    async def submit_phrase(
        self, user_id: str, match_id: str, phrase: str, secret_score: int
    ) -> Turn:
        """Registra frase y puntaje secreto y abre la votación (RF-TUR-003/004/006)."""
        match = self._matches.get_match(match_id)
        turn = self._active_turn(match)
        if turn is None:
            raise ApiError(409, "TURN_FINISHED", "No hay un turno en curso.")
        now = self._now()
        if turn.state == "active" and now > turn.expires_at:
            await self._close_and_advance(match, turn, expired_from="active")
            raise ApiError(409, "TURN_EXPIRED", "El tiempo del autor expiró.")
        if turn.state != "active":
            raise ApiError(409, "ALREADY_SUBMITTED", "La frase ya fue registrada.")
        if user_id != turn.author_id:
            raise ApiError(403, "NOT_AUTHOR", "Solo el autor puede completar la frase.")
        if not 3 <= len(phrase) <= 200:
            raise ApiError(422, "PHRASE_INVALID", "La frase debe tener entre 3 y 200 caracteres.")
        if not 1 <= secret_score <= 10:
            raise ApiError(422, "SCORE_INVALID", "El puntaje debe estar entre 1 y 10.")
        turn.phrase = phrase
        turn.secret_score = secret_score
        turn.state = "voting"
        turn.voting_ends_at = now + self._settings.voting_timeout_seconds * 1000
        self._turns.update(turn)
        return turn

    async def submit_vote(self, user_id: str, match_id: str, score: int) -> Turn:
        """Registra el voto de un participante (RF-TUR-007)."""
        match = self._matches.get_match(match_id)
        turn = self._active_turn(match)
        if turn is None:
            raise ApiError(409, "TURN_FINISHED", "No hay un turno en curso.")
        now = self._now()
        if turn.state == "voting" and now > turn.voting_ends_at:
            await self._close_and_advance(match, turn, expired_from="voting")
            raise ApiError(409, "TURN_FINISHED", "El tiempo de votación expiró.")
        if turn.state != "voting":
            raise ApiError(409, "NOT_VOTING", "La votación no está abierta.")
        if user_id == turn.author_id:
            raise ApiError(409, "NOT_VOTING", "El autor no puede votar su propia frase.")
        if not any(p.id == user_id for p in match.players):
            raise ApiError(403, "NOT_IN_MATCH", "No perteneces a esta partida.")
        if any(v.voter_id == user_id for v in turn.votes):
            raise ApiError(409, "ALREADY_VOTED", "Ya emitiste tu voto.")
        if not 1 <= score <= 10:
            raise ApiError(422, "SCORE_INVALID", "El puntaje debe estar entre 1 y 10.")
        turn.votes.append(Vote(voter_id=user_id, value=score))
        voters = len(match.players) - 1
        if len(turn.votes) >= voters:
            self._finalize(turn, match)
            self._advance(match)
            await self._notify_turn_closed(match, turn, "voting")
            await self._notify_turn_advanced(match, turn)
        self._turns.update(turn)
        self._matches.update(match)
        return turn

    # ------------------------------------------------------------------ #
    # Internos
    # ------------------------------------------------------------------ #

    def _active_turn(self, match: Match) -> Turn | None:
        if match.state != "in_progress" or match.current_turn is None:
            return None
        return self.get_turn(match.current_turn)

    def _create_turn(self, match: Match) -> Turn:
        now = self._now()
        turn = Turn(
            turn_id=_new_turn_id(),
            match_id=match.match_id,
            author_id=match.turn_order[match.turn_index],
            state="active",
            phrase=None,
            secret_score=None,
            created_at=now,
            expires_at=now + self._settings.author_timeout_seconds * 1000,
            voting_ends_at=None,
            votes=[],
        )
        self._turns.add(turn)
        match.current_turn = turn.turn_id
        self._matches.update(match)
        return turn

    def _discard(self, turn: Turn) -> None:
        turn.state = "discarded"
        self._turns.update(turn)

    def _finalize(self, turn: Turn, match: Match) -> None:
        turn.state = "finished"
        self._scoring.apply_turn(turn, match)
        self._turns.update(turn)
        self._matches.update(match)

    def _advance(self, match: Match) -> None:
        match.current_turn = None
        self._matches.advance_round(match)
        if match.state == "in_progress":
            self._create_turn(match)