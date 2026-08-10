"""Entidades de dominio del sistema."""

from dataclasses import dataclass


@dataclass
class User:
    id: str
    username: str
    email: str
    password_hash: str
    verified: bool = False
    profile_image_url: str = ""
    created_at: int = 0
    failed_attempts: int = 0
    blocked_until: int | None = None


@dataclass
class Session:
    token_hash: str
    user_id: str
    created_at: int
    expires_at: int
    revoked: bool = False


@dataclass
class VerificationToken:
    token_hash: str
    user_id: str
    kind: str
    expires_at: int
    used: bool = False