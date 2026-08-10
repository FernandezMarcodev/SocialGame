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


@dataclass
class PlayerRef:
    id: str
    username: str
    joined_at: int


@dataclass
class Room:
    code: str
    creator_id: str
    modality_id: int
    state: str
    players: list[PlayerRef]
    min_players: int
    max_players: int
    created_at: int