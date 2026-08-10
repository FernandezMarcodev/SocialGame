"""Routers del módulo de salas (Apéndice B.2.3, RF-SAL)."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_rooms_service
from app.api.schemas import MatchStartOut, RoomCreateIn, RoomOut
from app.services.room_service import RoomService

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("", response_model=RoomOut, status_code=201)
def create_room(
    payload: RoomCreateIn,
    user=Depends(get_current_user),
    rooms: RoomService = Depends(get_rooms_service),
) -> RoomOut:
    return rooms.serialize(rooms.create_room(user, payload.modality_id))


@router.get("/{code}", response_model=RoomOut)
def get_room(
    code: str,
    user=Depends(get_current_user),
    rooms: RoomService = Depends(get_rooms_service),
) -> RoomOut:
    return rooms.serialize(rooms.get_room(code))


@router.post("/{code}/join", response_model=RoomOut)
def join_room(
    code: str,
    user=Depends(get_current_user),
    rooms: RoomService = Depends(get_rooms_service),
) -> RoomOut:
    return rooms.serialize(rooms.join_room(user, code))


@router.post("/{code}/leave", response_model=RoomOut)
def leave_room(
    code: str,
    user=Depends(get_current_user),
    rooms: RoomService = Depends(get_rooms_service),
) -> RoomOut:
    return rooms.serialize(rooms.leave_room(user, code))


@router.post("/{code}/start", response_model=MatchStartOut)
def start_match(
    code: str,
    user=Depends(get_current_user),
    rooms: RoomService = Depends(get_rooms_service),
) -> MatchStartOut:
    return MatchStartOut(**rooms.start_match(user, code))


@router.delete("/{code}", status_code=204)
def cancel_room(
    code: str,
    user=Depends(get_current_user),
    rooms: RoomService = Depends(get_rooms_service),
) -> None:
    rooms.cancel_room(user, code)
    return None