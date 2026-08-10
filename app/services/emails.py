"""Composición de correos del módulo de cuentas."""

from app.domain.entities import User
from app.email.provider import EmailProvider

VERIFICATION_BASE_URL = "https://es10p.app/verify"


def send_verification(provider: EmailProvider, user: User, token: str) -> None:
    body = (
        f"Hola {user.username}:\n\n"
        f"Tu código de verificación es: {token}\n"
        f"Puedes verificarlo desde: {VERIFICATION_BASE_URL}?token={token}\n"
    )
    provider.send(user.email, "Verificación de correo — Es un 10 pero…", body)


def send_password_reset(provider: EmailProvider, user: User, token: str) -> None:
    body = (
        f"Hola {user.username}:\n\n"
        f"Tu código para restablecer la contraseña es: {token}\n"
    )
    provider.send(user.email, "Recuperación de contraseña — Es un 10 pero…", body)