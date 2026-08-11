"""Servicio de puntuación.

Implementa RF-PUN-001 a 004 según los contratos del Apéndice B.2.6 del DDD.
Reglas de negocio: RN-018 (solo el autor suma puntos) y RN-019 (un punto por
acierto exacto del puntaje secreto).
"""

from app.api.errors import ApiError
from app.domain.entities import Match, Turn
from app.services.match_service import MatchService


class ScoringService:
    def __init__(self, matches: MatchService) -> None:
        self._matches = matches

    def turn_points(self, turn: Turn) -> int:
        """Calcula los puntos del turno (RF-PUN-001)."""
        if turn.state not in ("finished", "discarded") or turn.secret_score is None:
            raise ApiError(
                409, "TURN_NOT_FINISHED", "La votación del turno aún no finalizó."
            )
        return sum(1 for v in turn.votes if v.value == turn.secret_score)

    def apply_turn(self, turn: Turn, match: Match) -> None:
        """Suma los puntos del turno al marcador del autor (RF-PUN-002)."""
        if match.state == "finished":
            raise ApiError(409, "MATCH_FINISHED", "La partida ya finalizó.")
        points = self.turn_points(turn)
        turn.points = points
        match.scores[turn.author_id] = match.scores.get(turn.author_id, 0) + points

    def scoreboard(self, match_id: str) -> dict:
        """Consulta el marcador actual (RF-PUN-003)."""
        match = self._matches.get_match(match_id)
        return {
            "round": match.turn_index,
            "scores": dict(sorted(match.scores.items(), key=lambda kv: kv[1], reverse=True)),
        }

    def result(self, match_id: str) -> dict:
        """Genera el resultado final (RF-PUN-004, RF-PAR-007)."""
        return self._matches.result(match_id)