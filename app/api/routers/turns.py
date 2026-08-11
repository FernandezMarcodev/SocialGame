"""Routers del módulo de turnos (Apéndice B.2.5, RF-TUR)."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_matches_service, get_turns_service
from app.api.errors import ApiError
from app.api.schemas import PhraseIn, TurnIdOut, TurnOut, VoteIn
from app.services.match_service import MatchService
from app.services.turn_service import TurnService

router = APIRouter(prefix="/matches", tags=["turns"])


@router.post("/{match_id}/phrase", response_model=TurnIdOut)
def submit_phrase(
    match_id: str,
    payload: PhraseIn,
    user=Depends(get_current_user),
    turns: TurnService = Depends(get_turns_service),
) -> TurnIdOut:
    turn = turns.submit_phrase(user.id, match_id, payload.phrase, payload.secret_score)
    return TurnIdOut(turn_id=turn.turn_id)


@router.post("/{match_id}/votes", response_model=TurnIdOut)
def submit_vote(
    match_id: str,
    payload: VoteIn,
    user=Depends(get_current_user),
    turns: TurnService = Depends(get_turns_service),
) -> TurnIdOut:
    turn = turns.submit_vote(user.id, match_id, payload.score)
    return TurnIdOut(turn_id=turn.turn_id)


@router.get("/{match_id}/turns/{turn_id}", response_model=TurnOut)
def get_turn(
    match_id: str,
    turn_id: str,
    user=Depends(get_current_user),
    turns: TurnService = Depends(get_turns_service),
    matches: MatchService = Depends(get_matches_service),
) -> TurnOut:
    match = matches.get_match(match_id)
    if not any(p.id == user.id for p in match.players):
        raise ApiError(403, "NOT_IN_MATCH", "No perteneces a esta partida.")
    turns.settle_expired(match_id)
    return turns.serialize_turn(turns.get_turn(turn_id))