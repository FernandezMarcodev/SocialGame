"""Catálogos precargados de modalidades y avatares (AD-007)."""

from app.api.schemas import ModalityOut

MODALITIES: list[ModalityOut] = [
    ModalityOut(id=1, name="Es un 10 pero...", template="Es un 10 pero ..."),
    ModalityOut(id=2, name="Es un 1 pero...", template="Es un 1 pero ..."),
]


def get_modality(modality_id: int) -> ModalityOut | None:
    return next((m for m in MODALITIES if m.id == modality_id), None)


def list_modalities() -> dict:
    return {"items": list(MODALITIES), "total": len(MODALITIES)}


# Avatares predeterminados - cada uno es un SVG generado con inicial + color
AVATARS: list[dict] = [
    {"id": "avatar-1", "label": "Rojo", "bg": "#e53e3e", "fg": "#fff"},
    {"id": "avatar-2", "label": "Naranja", "bg": "#dd6b20", "fg": "#fff"},
    {"id": "avatar-3", "label": "Amarillo", "bg": "#d69e2e", "fg": "#1a202c"},
    {"id": "avatar-4", "label": "Verde", "bg": "#38a169", "fg": "#fff"},
    {"id": "avatar-5", "label": "Verde azulado", "bg": "#319795", "fg": "#fff"},
    {"id": "avatar-6", "label": "Azul", "bg": "#3182ce", "fg": "#fff"},
    {"id": "avatar-7", "label": "Índigo", "bg": "#553c9a", "fg": "#fff"},
    {"id": "avatar-8", "label": "Morado", "bg": "#805ad5", "fg": "#fff"},
    {"id": "avatar-9", "label": "Rosa", "bg": "#d53f8c", "fg": "#fff"},
    {"id": "avatar-10", "label": "Cian", "bg": "#00b5d8", "fg": "#fff"},
    {"id": "avatar-11", "label": "Gris", "bg": "#718096", "fg": "#fff"},
    {"id": "avatar-12", "label": "Negro", "bg": "#1a202c", "fg": "#fff"},
]


def get_avatar(avatar_id: str) -> dict | None:
    return next((a for a in AVATARS if a["id"] == avatar_id), None)


def list_avatars() -> dict:
    return {"items": AVATARS, "total": len(AVATARS)}