"""Punto de entrada de la API del juego "Es un 10 pero…"."""

from fastapi import FastAPI

app = FastAPI(
    title="Es un 10 pero…",
    description="Videojuego multijugador por turnos — API REST",
    version="0.1.0",
)


@app.get("/")
def root() -> dict:
    """Información básica de la API."""
    return {"name": "Es un 10 pero…", "version": "0.1.0"}


@app.get("/health")
def health() -> dict:
    """Health check para monitorear que el servidor está operativo."""
    return {"status": "ok"}