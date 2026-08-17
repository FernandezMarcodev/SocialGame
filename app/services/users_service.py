"""Servicio de usuarios.

Implementa los RF-USR-005 a 007.
"""

import glob
import os
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig

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
        self._s3_client: Optional[boto3.client] = None
        if settings.avatar_storage == "s3" and settings.s3_endpoint_url and settings.s3_bucket:
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region,
                config=BotoConfig(s3={"addressing_style": "path"}),
            )

    def _avatar_key(self, user_id: str, ext: str) -> str:
        return f"avatars/{user_id}{ext}"

    def _avatar_public_url(self, key: str) -> str:
        if self._settings.s3_public_url:
            return f"{self._settings.s3_public_url.rstrip('/')}/{key}"
        if self._s3_client and self._settings.s3_endpoint_url:
            return f"{self._settings.s3_endpoint_url.rstrip('/')}/{self._settings.s3_bucket}/{key}"
        return f"/uploads/{key}"

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

        - Si avatar_storage == "s3": sube a bucket S3-compatible (persistente multi-instancia)
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

        key = self._avatar_key(user.id, ext)

        if self._s3_client:
            # Borrar avatar anterior si existe
            try:
                self._s3_client.delete_object(Bucket=self._settings.s3_bucket, Key=key)
            except Exception:
                pass
            # Subir nuevo
            self._s3_client.put_object(
                Bucket=self._settings.s3_bucket,
                Key=key,
                Body=content,
                ContentType=content_type,
                ACL="public-read",
            )
        else:
            # Local filesystem (dev / single instance)
            os.makedirs(self._settings.upload_dir, exist_ok=True)
            for old in glob.glob(os.path.join(self._settings.upload_dir, f"{user.id}.*")):
                os.remove(old)
            with open(os.path.join(self._settings.upload_dir, f"{user.id}{ext}"), "wb") as f:
                f.write(content)

        user.profile_image_url = self._avatar_public_url(key)
        self._users.update(user)
        return UserOut.model_validate(user)
