"""Utilidades de seguridad: hash de contraseñas (Argon2id) y tokens opacos.

Implementa las decisiones AD-002 (token opaco con hash) y AD-006 (Argon2id).
"""

import hashlib
import re
import secrets
import time

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

PASSWORD_MIN_LENGTH = 8
_PASSWORD_PATTERNS = (r"[A-Z]", r"[a-z]", r"[0-9]", r"[^A-Za-z0-9]")


def utcnow_ms() -> int:
    """Devuelve la hora actual en epoch milisegundos (UTC)."""
    return int(time.time() * 1000)


class PasswordHasherArgon2:
    """Hashes de contraseña con Argon2id (AD-006)."""

    def __init__(self) -> None:
        self._hasher = PasswordHasher()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except VerifyMismatchError:
            return False
        except Exception:
            return False


def validate_password_policy(password: str) -> str | None:
    """Valida la política de contraseñas (AD-010).

    Devuelve el mensaje de error o ``None`` si la contraseña es válida.
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return f"La contraseña debe tener al menos {PASSWORD_MIN_LENGTH} caracteres."
    for pattern in _PASSWORD_PATTERNS:
        if re.search(pattern, password) is None:
            return "La contraseña debe incluir mayúscula, minúscula, dígito y símbolo."
    return None


def generate_token() -> str:
    """Genera un token opaco aleatorio (AD-002)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Calcula el hash del token para almacenarlo sin exponer su valor (AD-002)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()