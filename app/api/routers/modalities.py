"""Routers del catálogo de modalidades (AD-007)."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_users_service
from app.services.users_service import UsersService

router = APIRouter(prefix="/modalities", tags=["modalities"])


@router.get("")
def list_modalities(
    user=Depends(get_current_user),
    users: UsersService = Depends(get_users_service),
) -> dict:
    return users.list_modalities()