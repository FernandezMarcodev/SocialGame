"""Routers del módulo de puntuación (Apéndice B.2.6, RF-PUN)."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_scoring_service, get_turns_service
from app.api.schemas import ResultOut, ScoreboardOut
from app.services.scoring_service import ScoringService
from app.services.turn_service import TurnService

router = APIRouter(prefix="/matches", tags=["scoring"])


@router.get("/{match_id}/scoreboard", response_model=ScoreboardOut)
def get_scoreboard(
    match_id: str,
    user=Depends(get_current_user),
    scoring: ScoringService = Depends(get_scoring_service),
    turns: TurnService = Depends(get_turns_service),
) -> ScoreboardOut:
    turns.settle_expired(match_id)
    return ScoreboardOut(**scoring.scoreboard(match_id))


@router.get("/{match_id}/result", response_model=ResultOut)
def get_result(
    match_id: str,
    user=Depends(get_current_user),
    scoring: ScoringService = Depends(get_scoring_service),
    turns: TurnService = Depends(get_turns_service),
) -> ResultOut:
    turns.settle_expired(match_id)
    return ResultOut(**scoring.result(match_id))