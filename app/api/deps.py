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


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    auth_service=Depends(get_auth_service),
) -> User:
    if credentials is None:
        raise ApiError(401, "TOKEN_INVALID", "Token inválido.")
    return auth_service.resolve_access_token(credentials.credentials)