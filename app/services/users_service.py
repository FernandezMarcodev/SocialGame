"""Servicio de usuarios y catálogo de modalidades.

Implementa los RF-USR-005 a 007 y el catálogo precargado de AD-007.
"""

from app.api.errors import ApiError
from app.api.schemas import UserOut
from app.domain.entities import User
from app.services.auth_service import _profile_image_url
from app.services.catalog import MODALITIES
from app.stores.base import UserStore


class UsersService:
    def __init__(self, users: UserStore, auth_service) -> None:
        self._users = users
        self._auth = auth_service

    def update_profile(self, user: User, username: str | None, email: str | None) -> UserOut:
        if username is not None and username != user.username:
            existing = self._users.get_by_username(username)
            if existing is not None and existing.id != user.id:
                raise ApiError(
                    409, "USERNAME_TAKEN", "El nombre de usuario ya se encuentra registrado."
                )
            user.username = username
            user.profile_image_url = _profile_image_url(username)
        if email is not None and email.lower() != user.email.lower():
            existing = self._users.get_by_email(email)
            if existing is not None and existing.id != user.id:
                raise ApiError(
                    409, "EMAIL_TAKEN", "El correo electrónico ya se encuentra registrado."
                )
            user.email = email
            user.verified = False
            self._auth.issue_verification(user)
        self._users.update(user)
        return UserOut.model_validate(user)

    def list_modalities(self) -> dict:
        return {"items": list(MODALITIES), "total": len(MODALITIES)}