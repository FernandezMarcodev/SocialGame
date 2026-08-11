"""Router del catálogo de modalidades (AD-007)."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.services.catalog import list_modalities

router = APIRouter(prefix="/modalities", tags=["modalities"])


@router.get("")
def get_modalities(
    user=Depends(get_current_user),
) -> dict:
    return list_modalities()