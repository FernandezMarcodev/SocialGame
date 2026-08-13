"""Routers del módulo de partidas (Apéndice B.2.4, RF-PAR)."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_matches_service, get_turns_service
from app.api.schemas import MatchOut
from app.services.match_service import MatchService
from app.services.turn_service import TurnService

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/by-room/{code}", response_model=MatchOut)
def get_match_by_room(
    code: str,
    user=Depends(get_current_user),
    matches: MatchService = Depends(get_matches_service),
    turns: TurnService = Depends(get_turns_service),
) -> MatchOut:
    match = matches.get_match_by_room(code)
    turns.settle_expired(match.match_id)
    return matches.serialize(match)


@router.get("/{match_id}", response_model=MatchOut)
def get_match(
    match_id: str,
    user=Depends(get_current_user),
    matches: MatchService = Depends(get_matches_service),
    turns: TurnService = Depends(get_turns_service),
) -> MatchOut:
    turns.settle_expired(match_id)
    return matches.serialize(matches.get_match(match_id))