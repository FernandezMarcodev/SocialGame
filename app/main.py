"""Punto de entrada de la API del juego "Es un 10 pero…"."""

from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Videojuego multijugador por turnos — API REST",
    version=settings.app_version,
)


@app.get("/")
def root() -> dict:
    """Información básica de la API."""
    return {"name": "Es un 10 pero…", "version": "0.1.0"}


@app.get("/health")
def health() -> dict:
    """Health check para monitorear que el servidor está operativo."""
    return {"status": "ok"}