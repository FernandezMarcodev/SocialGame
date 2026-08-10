"""Routers del módulo de autenticación (Apéndice B.2.1)."""

from fastapi import APIRouter, Depends

from app.api.deps import bearer, get_auth_service, get_current_user
from app.api.schemas import (
    ChangePasswordIn,
    ForgotPasswordIn,
    LoginIn,
    RegisterIn,
    ResetPasswordIn,
    TokenOut,
    UserOut,
    VerifyEmailIn,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterIn, auth: AuthService = Depends(get_auth_service)) -> UserOut:
    return auth.register(payload.username, payload.email, payload.password)


@router.post("/verify-email", status_code=200)
def verify_email(payload: VerifyEmailIn, auth: AuthService = Depends(get_auth_service)) -> dict:
    auth.verify_email(payload.token)
    return {}


@router.post("/resend-verification", status_code=200)
def resend_verification(
    payload: ForgotPasswordIn, auth: AuthService = Depends(get_auth_service)
) -> dict:
    auth.resend_verification(payload.email)
    return {}


@router.post("/login", response_model=TokenOut, status_code=200)
def login(payload: LoginIn, auth: AuthService = Depends(get_auth_service)) -> TokenOut:
    return auth.login(payload.identifier, payload.password)


@router.post("/logout", status_code=204)
def logout(
    credentials=Depends(bearer),
    user=Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
) -> None:
    auth.logout(credentials.credentials)
    return None


@router.post("/change-password", status_code=200)
def change_password(
    payload: ChangePasswordIn,
    user=Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
) -> dict:
    auth.change_password(user.id, payload.current_password, payload.new_password)
    return {}


@router.post("/forgot-password", status_code=200)
def forgot_password(
    payload: ForgotPasswordIn, auth: AuthService = Depends(get_auth_service)
) -> dict:
    auth.forgot_password(payload.email)
    return {}


@router.post("/reset-password", status_code=200)
def reset_password(
    payload: ResetPasswordIn, auth: AuthService = Depends(get_auth_service)
) -> dict:
    auth.reset_password(payload.token, payload.new_password)
    return {}