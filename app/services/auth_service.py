"""Servicio de autenticación y cuentas.

Implementa las reglas de negocio RN-001 a RN-004 y los RF-AUT-001 a 009 según
los contratos del Apéndice B.2.1 del DDD.
"""

import logging
from typing import Callable
from uuid import uuid4

from app.api.errors import ApiError
from app.api.schemas import TokenOut, UserOut
from app.core.config import Settings
from app.core.security import (
    PasswordHasherArgon2,
    generate_token,
    hash_token,
    utcnow_ms,
    validate_password_policy,
)
from app.domain.avatars import avatar_url
from app.domain.entities import Session, User, VerificationToken
from app.email.provider import EmailProvider
from app.services.emails import send_password_reset
from app.stores.base import SessionStore, UserStore, VerificationStore


def _new_user_id() -> str:
    return "usr-" + uuid4().hex[:10]


logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        settings: Settings,
        users: UserStore,
        sessions: SessionStore,
        verifications: VerificationStore,
        emails: EmailProvider,
        hasher: PasswordHasherArgon2 | None = None,
        now: Callable[[], int] | None = None,
    ) -> None:
        self._settings = settings
        self._users = users
        self._sessions = sessions
        self._verifications = verifications
        self._emails = emails
        self._hasher = hasher or PasswordHasherArgon2()
        self._now = now or utcnow_ms

    def register(self, username: str, email: str, password: str) -> UserOut:
        policy_error = validate_password_policy(password)
        if policy_error is not None:
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "Los datos enviados no son válidos.",
                {"password": policy_error},
            )
        if self._users.get_by_username(username) is not None:
            raise ApiError(
                409, "USERNAME_TAKEN", "El nombre de usuario ya se encuentra registrado."
            )
        if self._users.get_by_email(email) is not None:
            raise ApiError(
                409, "EMAIL_TAKEN", "El correo electrónico ya se encuentra registrado."
            )
        user = User(
            id=_new_user_id(),
            username=username,
            email=email,
            password_hash=self._hasher.hash(password),
            profile_image_url=avatar_url(username),
            created_at=self._now(),
        )
        self._users.add(user)
        return UserOut.model_validate(user)

    def login(self, identifier: str, password: str) -> TokenOut:
        user = (
            self._users.get_by_username(identifier)
            or self._users.get_by_email(identifier)
        )
        if user is None:
            raise ApiError(401, "INVALID_CREDENTIALS", "Credenciales inválidas.")
        now = self._now()
        if user.blocked_until is not None and user.blocked_until > now:
            retry_after = max(1, (user.blocked_until - now) // 1000)
            raise ApiError(
                423,
                "ACCOUNT_BLOCKED",
                "Cuenta bloqueada temporalmente.",
                {"retry_after": retry_after},
            )
        if not self._hasher.verify(password, user.password_hash):
            user.failed_attempts += 1
            if user.failed_attempts >= self._settings.max_login_attempts:
                user.blocked_until = now + self._settings.lockout_seconds * 1000
                user.failed_attempts = 0
                self._users.update(user)
                raise ApiError(
                    423,
                    "ACCOUNT_BLOCKED",
                    "Cuenta bloqueada temporalmente.",
                    {"retry_after": self._settings.lockout_seconds},
                )
            self._users.update(user)
            raise ApiError(401, "INVALID_CREDENTIALS", "Credenciales inválidas.")
        user.failed_attempts = 0
        user.blocked_until = None
        self._users.update(user)
        token = generate_token()
        expires_at = now + self._settings.token_ttl_seconds * 1000
        self._sessions.add(
            Session(
                token_hash=hash_token(token),
                user_id=user.id,
                created_at=now,
                expires_at=expires_at,
            )
         )
        logger.info("login exitoso: %s (id=%s)", user.username, user.id)
        return TokenOut(
            access_token=token,
            expires_at=expires_at,
            user=UserOut.model_validate(user),
        )

    def logout(self, access_token: str) -> None:
        self._sessions.revoke(hash_token(access_token))

    def change_password(self, user_id: str, current: str, new: str) -> None:
        policy_error = validate_password_policy(new)
        if policy_error is not None:
            raise ApiError(400, "PASSWORD_POLICY", policy_error)
        user = self._users.get_by_id(user_id)
        if user is None or not self._hasher.verify(current, user.password_hash):
            raise ApiError(401, "INVALID_CREDENTIALS", "Contraseña actual incorrecta.")
        user.password_hash = self._hasher.hash(new)
        self._users.update(user)

    def forgot_password(self, email: str) -> None:
        user = self._users.get_by_email(email)
        if user is None:
            return
        token = generate_token()
        self._verifications.add(
            VerificationToken(
                token_hash=hash_token(token),
                user_id=user.id,
                kind="reset",
                expires_at=self._now() + self._settings.reset_token_ttl_seconds * 1000,
            )
        )
        send_password_reset(self._emails, user, token)

    def reset_password(self, token: str, new_password: str) -> None:
        policy_error = validate_password_policy(new_password)
        if policy_error is not None:
            raise ApiError(400, "PASSWORD_POLICY", policy_error)
        verification = self._verifications.get(hash_token(token))
        if verification is None or verification.used or verification.kind != "reset":
            raise ApiError(400, "TOKEN_INVALID", "El token no es válido.")
        if verification.expires_at <= self._now():
            raise ApiError(400, "TOKEN_EXPIRED", "El token ha expirado.")
        user = self._users.get_by_id(verification.user_id)
        if user is None:
            raise ApiError(400, "TOKEN_INVALID", "El token no es válido.")
        user.password_hash = self._hasher.hash(new_password)
        self._users.update(user)
        self._verifications.mark_used(verification.token_hash)

    def resolve_access_token(self, access_token: str) -> User:
        session = self._sessions.get(hash_token(access_token))
        if session is None or session.revoked:
            raise ApiError(401, "TOKEN_INVALID", "Token inválido.")
        if session.expires_at <= self._now():
            raise ApiError(401, "TOKEN_EXPIRED", "La sesión ha expirado.")
        user = self._users.get_by_id(session.user_id)
        if user is None:
            raise ApiError(401, "TOKEN_INVALID", "Token inválido.")
        return user