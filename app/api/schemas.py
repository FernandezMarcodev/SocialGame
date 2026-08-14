"""Schemas Pydantic de entrada y salida de la API."""

from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
)

UsernameType = Annotated[
    str,
    StringConstraints(min_length=3, max_length=20, pattern=r"^[A-Za-z0-9_.-]+$"),
]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: EmailStr
    verified: bool
    profile_image_url: str
    created_at: int


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: int
    user: UserOut


class RegisterIn(BaseModel):
    username: UsernameType
    email: EmailStr
    password: str = Field(min_length=8)


class LoginIn(BaseModel):
    identifier: str
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class VerifyEmailIn(BaseModel):
    token: str


class UpdateProfileIn(BaseModel):
    username: UsernameType | None = None
    email: EmailStr | None = None


class ModalityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    template: str


class RoomCreateIn(BaseModel):
    modality_id: int


class PlayerOut(BaseModel):
    id: str
    username: str
    joined_at: int
    profile_image_url: str = ""


class RoomOut(BaseModel):
    code: str
    state: str
    creator_id: str
    modality: ModalityOut
    players: list[PlayerOut]
    min_players: int
    max_players: int
    created_at: int


class MatchStartOut(BaseModel):
    match_id: str


class MatchOut(BaseModel):
    match_id: str
    room_code: str
    state: str
    players: list[PlayerOut]
    turn_order: list[str]
    current_turn: str | None
    scores: dict[str, int]
    created_at: int
    turn_index: int = 0
    total_rounds: int = 3


class PhraseIn(BaseModel):
    phrase: str = Field(min_length=3, max_length=200)
    secret_score: int = Field(ge=1, le=10)


class VoteIn(BaseModel):
    score: int = Field(ge=1, le=10)


class VoteOut(BaseModel):
    voter_id: str
    value: int


class TurnOut(BaseModel):
    turn_id: str
    match_id: str
    author_id: str
    state: str
    phrase: str | None
    secret_score: int | None
    created_at: int
    expires_at: int
    voting_ends_at: int | None
    votes: list[VoteOut]
    votes_count: int
    points: int


class TurnIdOut(BaseModel):
    turn_id: str


class ScoreboardOut(BaseModel):
    round: int
    scores: dict[str, int]


class ResultOut(BaseModel):
    winner_id: str | None
    tied: bool
    scores: dict[str, int]