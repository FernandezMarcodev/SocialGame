"""Catálogo precargado de modalidades de juego (AD-007).

Es la única fuente de ``modality_id`` para crear salas (RF-USR/RF-SAL) y la
modalidad queda fija durante la sesión (RN-011).
"""

from app.api.schemas import ModalityOut

MODALITIES: list[ModalityOut] = [
    ModalityOut(id=1, name="Es un 10 pero...", template="Es un 10 pero ..."),
    ModalityOut(id=2, name="Mi día es un 10 pero...", template="Mi día es un 10 pero ..."),
]


def get_modality(modality_id: int) -> ModalityOut | None:
    return next((m for m in MODALITIES if m.id == modality_id), None)