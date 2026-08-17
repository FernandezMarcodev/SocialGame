"""Configuración de la aplicación mediante variables de entorno (pydantic-settings)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Valores de configuración de la API.

    Se leen de variables de entorno y/o del archivo ``.env``.
    """

    app_name: str = "Es un 10 pero…"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = ""

    token_ttl_seconds: int = 86400
    reset_token_ttl_seconds: int = 3600
    max_login_attempts: int = 5
    lockout_seconds: int = 300
    email_provider: str = "console"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""
    gmail_from: str = ""

    room_min_players: int = 2
    room_max_players: int = 6
    author_timeout_seconds: int = 90
    voting_timeout_seconds: int = 45

    upload_dir: str = "uploads"
    max_avatar_bytes: int = 2_000_000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración cacheada de la aplicación."""
    return Settings()