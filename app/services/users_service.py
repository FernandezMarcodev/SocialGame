"""Servicio de usuarios.

Implementa los RF-USR-005 a 007.
"""

import glob
import os

from app.api.errors import ApiError
from app.api.schemas import UserOut
from app.domain.entities import User
from app.services.auth_service import AuthService
from app.stores.base import UserStore

ALLOWED_AVATAR_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


class UsersService:
    def __init__(
        self,
        users: UserStore,
        auth_service: AuthService,
        upload_dir: str = "uploads",
        max_avatar_bytes: int = 2_000_000,
    ) -> None:
        self._users = users
        self._auth = auth_service
        self._upload_dir = upload_dir
        self._max_avatar_bytes = max_avatar_bytes

    def update_profile(self, user: User, username: str | None, email: str | None) -> UserOut:
        if username is not None and username != user.username:
            existing = self._users.get_by_username(username)
            if existing is not None and existing.id != user.id:
                raise ApiError(
                    409, "USERNAME_TAKEN", "El nombre de usuario ya se encuentra registrado."
                )
            user.username = username
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

    def update_avatar(self, user: User, content: bytes, content_type: str | None) -> UserOut:
        """Guarda la foto de perfil subida y la sirve desde /uploads (RF-USR-007)."""
        ext = ALLOWED_AVATAR_TYPES.get(content_type or "")
        if ext is None:
            raise ApiError(415, "UNSUPPORTED_IMAGE_TYPE", "La foto debe ser JPG, PNG, WEBP o GIF.")
        if not content:
            raise ApiError(400, "EMPTY_IMAGE", "El archivo de imagen está vacío.")
        if len(content) > self._max_avatar_bytes:
            raise ApiError(
                413,
                "IMAGE_TOO_LARGE",
                f"La foto supera el tamaño máximo ({self._max_avatar_bytes // 1_000_000} MB).",
            )

        os.makedirs(self._upload_dir, exist_ok=True)
        for old in glob.glob(os.path.join(self._upload_dir, f"{user.id}.*")):
            os.remove(old)
        filename = f"{user.id}{ext}"
        with open(os.path.join(self._upload_dir, filename), "wb") as f:
            f.write(content)

        user.profile_image_url = f"/uploads/{filename}"
        self._users.update(user)
        return UserOut.model_validate(user)
