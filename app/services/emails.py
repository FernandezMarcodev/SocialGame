"""Composición de correos del módulo de cuentas."""

from app.domain.entities import User
from app.email.provider import EmailProvider


def send_password_reset(provider: EmailProvider, user: User, token: str) -> None:
    body = (
        f"Hola {user.username}:\n\n"
        f"Tu código para restablecer la contraseña es: {token}\n"
    )
    provider.send(user.email, "Recuperación de contraseña — Es un 10 pero…", body)