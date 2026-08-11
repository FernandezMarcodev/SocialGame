"""Catálogo precargado de modalidades de juego (AD-007).

Es la única fuente de ``modality_id`` para crear salas (RF-USR/RF-SAL) y la
modalidad queda fija durante la sesión (RN-011).
"""

from app.api.schemas import ModalityOut

MODALITIES: list[ModalityOut] = [
    ModalityOut(id=1, name="Es un 10 pero...", template="Es un 10 pero ..."),
    ModalityOut(id=2, name="Es un 1 pero...", template="Es un 1 pero ..."),
]


def get_modality(modality_id: int) -> ModalityOut | None:
    return next((m for m in MODALITIES if m.id == modality_id), None)


def list_modalities() -> dict:
    return {"items": list(MODALITIES), "total": len(MODALITIES)}