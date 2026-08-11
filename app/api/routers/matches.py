"""Routers del módulo de partidas (Apéndice B.2.4, RF-PAR)."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_matches_service
from app.api.schemas import MatchOut
from app.services.match_service import MatchService

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/{match_id}", response_model=MatchOut)
def get_match(
    match_id: str,
    user=Depends(get_current_user),
    matches: MatchService = Depends(get_matches_service),
) -> MatchOut:
    return matches.serialize(matches.get_match(match_id))