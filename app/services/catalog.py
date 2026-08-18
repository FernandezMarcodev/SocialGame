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


# Avatares predeterminados - URLs de imágenes simples (emojis/ilustraciones)
# En producción podrías subir imágenes reales a un CDN/S3
AVATARS: list[dict] = [
    {"id": "avatar-1", "label": "Gato", "image_url": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f408.png"},
    {"id": "avatar-2", "label": "Perro", "image_url": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f415.png"},
    {"id": "avatar-3", "label": "Conejo", "image_url": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f407.png"},
    {"id": "avatar-4", "label": "Zorro", "image_url": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f98a.png"},
    {"id": "avatar-5", "label": "Oso", "image_url": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f43b.png"},
    {"id": "avatar-6", "label": "Panda", "image_url": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f43c.png"},
    {"id": "avatar-7", "label": "Koala", "image_url": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f428.png"},
    {"id": "avatar-8", "label": "Tigre", "image_url": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f42f.png"},
    {"id": "avatar-9", "label": "León", "image_url": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f981.png"},
    {"id": "avatar-10", "label": "Mono", "image_url": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f412.png"},
    {"id": "avatar-11", "label": "Pingüino", "image_url": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f427.png"},
    {"id": "avatar-12", "label": "Unicornio", "image_url": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f984.png"},
]


def get_avatar(avatar_id: str) -> dict | None:
    return next((a for a in AVATARS if a["id"] == avatar_id), None)


def list_avatars() -> dict:
    return {"items": AVATARS, "total": len(AVATARS)}