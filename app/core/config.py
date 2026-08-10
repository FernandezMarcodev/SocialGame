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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración cacheada de la aplicación."""
    return Settings()