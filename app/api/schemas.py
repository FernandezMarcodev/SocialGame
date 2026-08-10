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