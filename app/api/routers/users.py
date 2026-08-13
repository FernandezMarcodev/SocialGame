"""Routers del módulo de usuarios (Apéndice B.2.2)."""

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_current_user, get_users_service
from app.api.schemas import UpdateProfileIn, UserOut
from app.services.users_service import UsersService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(user=Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UpdateProfileIn,
    user=Depends(get_current_user),
    users: UsersService = Depends(get_users_service),
) -> UserOut:
    return users.update_profile(user, payload.username, payload.email)


@router.put("/me/avatar", response_model=UserOut)
async def update_avatar(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    users: UsersService = Depends(get_users_service),
) -> UserOut:
    content = await file.read()
    return users.update_avatar(user, content, file.content_type)