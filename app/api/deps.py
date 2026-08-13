from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.api.errors import ApiError
from app.domain.entities import User

bearer = HTTPBearer(auto_error=False)


def get_auth_service(request: Request):
    return request.app.state.auth_service


def get_users_service(request: Request):
    return request.app.state.users_service


def get_rooms_service(request: Request):
    return request.app.state.rooms_service


def get_matches_service(request: Request):
    return request.app.state.matches_service


def get_turns_service(request: Request):
    return request.app.state.turns_service


def get_scoring_service(request: Request):
    return request.app.state.scoring_service


def get_event_bus(request: Request):
    return request.app.state.event_bus


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    auth_service=Depends(get_auth_service),
) -> User:
    if credentials is None:
        raise ApiError(401, "TOKEN_INVALID", "Token inválido.")
    return auth_service.resolve_access_token(credentials.credentials)