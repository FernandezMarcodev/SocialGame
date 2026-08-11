"""Generación de la URL de avatar por perfil de usuario."""


def avatar_url(username: str) -> str:
    initial = username[0].lower() if username else "x"
    return f"/avatars/{initial}.svg"