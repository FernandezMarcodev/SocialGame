"""Servicio de usuarios.

Implementa los RF-USR-005 a 007.
"""

import base64
import glob
import os
from typing import Optional

from app.api.errors import ApiError
from app.api.schemas import UserOut
from app.core.config import Settings
from app.domain.entities import User
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
        settings: Settings,
    ) -> None:
        self._users = users
        self._settings = settings
        # Backward compat para tests
        self._upload_dir = settings.upload_dir
        self._max_avatar_bytes = settings.max_avatar_bytes

    def _avatar_data_url(self, user: User) -> str:
        """Genera data URL para avatar guardado en DB."""
        if hasattr(user, 'avatar_data') and user.avatar_data and hasattr(user, 'avatar_content_type') and user.avatar_content_type:
            b64 = base64.b64encode(user.avatar_data).decode('ascii')
            return f"data:{user.avatar_content_type};base64,{b64}"
        return user.profile_image_url or ""

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
        self._users.update(user)
        return UserOut.model_validate(user)

    def update_avatar(self, user: User, content: bytes, content_type: str | None) -> UserOut:
        """Guarda la foto de perfil subida (RF-USR-007).

        - Si avatar_storage == "database": guarda bytes en PostgreSQL (persistente multi-instancia)
        - Si "local": guarda en filesystem local (solo 1 instancia, se pierde al reiniciar contenedor)
        """
        ext = ALLOWED_AVATAR_TYPES.get(content_type or "")
        if ext is None:
            raise ApiError(415, "UNSUPPORTED_IMAGE_TYPE", "La foto debe ser JPG, PNG, WEBP o GIF.")
        if not content:
            raise ApiError(400, "EMPTY_IMAGE", "El archivo de imagen está vacío.")
        if len(content) > self._settings.max_avatar_bytes:
            raise ApiError(
                413,
                "IMAGE_TOO_LARGE",
                f"La foto supera el tamaño máximo ({self._settings.max_avatar_bytes // 1_000_000} MB).",
            )

        if self._settings.avatar_storage == "database":
            # Guardar en DB como bytes
            user.avatar_data = content
            user.avatar_content_type = content_type
            # profile_image_url apunta a endpoint que sirve la imagen desde DB
            user.profile_image_url = f"/api/v1/users/me/avatar/image"
        else:
            # Local filesystem (dev / single instance)
            os.makedirs(self._settings.upload_dir, exist_ok=True)
            for old in glob.glob(os.path.join(self._settings.upload_dir, f"{user.id}.*")):
                os.remove(old)
            filename = f"{user.id}{ext}"
            with open(os.path.join(self._settings.upload_dir, filename), "wb") as f:
                f.write(content)
            user.profile_image_url = f"/uploads/{filename}"

        self._users.update(user)
        return UserOut.model_validate(user)
