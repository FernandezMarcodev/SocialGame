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
    profile_image_url: str = ""


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


@dataclass
class Match:
    match_id: str
    room_code: str
    modality_id: int
    state: str
    players: list[PlayerRef]
    turn_order: list[str]
    turn_index: int
    current_turn: str | None
    scores: dict[str, int]
    created_at: int


@dataclass
class Vote:
    voter_id: str
    value: int


@dataclass
class Turn:
    turn_id: str
    match_id: str
    author_id: str
    state: str
    phrase: str | None
    secret_score: int | None
    created_at: int
    expires_at: int
    voting_ends_at: int | None
    votes: list[Vote]
    points: int = 0