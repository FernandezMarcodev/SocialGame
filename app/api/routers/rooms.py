"""Routers del módulo de salas (Apéndice B.2.3, RF-SAL)."""

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_current_user,
    get_event_bus,
    get_matches_service,
    get_rooms_service,
)
from app.api.schemas import MatchStartOut, RoomCreateIn, RoomOut
from app.services.match_service import MatchService
from app.services.realtime_service import EventBus
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
async def join_room(
    code: str,
    user=Depends(get_current_user),
    rooms: RoomService = Depends(get_rooms_service),
    bus: EventBus = Depends(get_event_bus),
) -> RoomOut:
    room = rooms.join_room(user, code)
    out = rooms.serialize(room)
    await bus.publish("room.updated", {"code": room.code, "room": out.model_dump()})
    return out


@router.post("/{code}/leave", response_model=RoomOut)
async def leave_room(
    code: str,
    user=Depends(get_current_user),
    rooms: RoomService = Depends(get_rooms_service),
    bus: EventBus = Depends(get_event_bus),
) -> RoomOut:
    room = rooms.leave_room(user, code)
    out = rooms.serialize(room)
    await bus.publish("room.updated", {"code": room.code, "room": out.model_dump()})
    return out


@router.post("/{code}/start", response_model=MatchStartOut)
async def start_match(
    code: str,
    user=Depends(get_current_user),
    rooms: RoomService = Depends(get_rooms_service),
    matches: MatchService = Depends(get_matches_service),
    bus: EventBus = Depends(get_event_bus),
) -> MatchStartOut:
    data = rooms.start_match(user, code)
    match = matches.get_match_by_room(code)
    await bus.publish(
        "match.started",
        {
            "match_id": match.match_id,
            "room_code": match.room_code,
            "order": list(match.turn_order),
            "first_author": match.turn_order[0] if match.turn_order else None,
        },
    )
    return MatchStartOut(**data)


@router.delete("/{code}", status_code=204)
async def cancel_room(
    code: str,
    user=Depends(get_current_user),
    rooms: RoomService = Depends(get_rooms_service),
    bus: EventBus = Depends(get_event_bus),
) -> None:
    room = rooms.get_room(code)
    rooms.cancel_room(user, code)
    await bus.publish("room.cancelled", {"code": room.code, "room": room})
    return None
