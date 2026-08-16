"""Implementaciones en memoria de los stores.

Mientras no exista persistencia (feature de PostgreSQL), la API usa almacenes
en memoria por proceso, coherente con AD-002/AD-003.
"""

from app.domain.entities import (
    Match,
    PlayerRef,
    Room,
    Session,
    Turn,
    User,
    VerificationToken,
    Vote,
)


class MemoryUserStore:
    def __init__(self) -> None:
        self._by_id: dict[str, User] = {}
        self._by_username: dict[str, User] = {}
        self._by_email: dict[str, User] = {}

    def add(self, user: User) -> None:
        self._by_id[user.id] = user
        self._by_username[user.username.lower()] = user
        self._by_email[user.email.lower()] = user

    def get_by_id(self, user_id: str) -> User | None:
        return self._by_id.get(user_id)

    def get_by_username(self, username: str) -> User | None:
        return self._by_username.get(username.lower())

    def get_by_email(self, email: str) -> User | None:
        return self._by_email.get(email.lower())

    def update(self, user: User) -> None:
        self._by_id[user.id] = user
        self._by_username[user.username.lower()] = user
        self._by_email[user.email.lower()] = user


class MemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def add(self, session: Session) -> None:
        self._sessions[session.token_hash] = session

    def get(self, token_hash: str) -> Session | None:
        return self._sessions.get(token_hash)

    def revoke(self, token_hash: str) -> None:
        session = self._sessions.get(token_hash)
        if session is not None:
            session.revoked = True


class MemoryVerificationStore:
    def __init__(self) -> None:
        self._tokens: dict[str, VerificationToken] = {}

    def add(self, token: VerificationToken) -> None:
        self._tokens[token.token_hash] = token

    def get(self, token_hash: str) -> VerificationToken | None:
        return self._tokens.get(token_hash)

    def mark_used(self, token_hash: str) -> None:
        token = self._tokens.get(token_hash)
        if token is not None:
            token.used = True


class MemoryRoomStore:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}
        self._player_room: dict[str, str] = {}

    def add(self, room: Room) -> None:
        self._rooms[room.code] = room
        for player in room.players:
            self._player_room[player.id] = room.code

    def get(self, code: str) -> Room | None:
        return self._rooms.get(code)

    def remove(self, code: str) -> None:
        room = self._rooms.pop(code, None)
        if room is not None:
            for player in room.players:
                self._player_room.pop(player.id, None)

    def get_room_by_player(self, user_id: str) -> Room | None:
        code = self._player_room.get(user_id)
        if code is None:
            return None
        return self._rooms.get(code)

    def add_player(self, code: str, player: PlayerRef) -> Room | None:
        room = self._rooms.get(code)
        if room is None:
            return None
        room.players.append(player)
        self._player_room[player.id] = code
        return room

    def remove_player(self, code: str, player_id: str) -> Room | None:
        room = self._rooms.get(code)
        if room is None:
            return None
        room.players = [p for p in room.players if p.id != player_id]
        self._player_room.pop(player_id, None)
        return room

    def set_creator(self, code: str, creator_id: str) -> Room | None:
        room = self._rooms.get(code)
        if room is None:
            return None
        room.creator_id = creator_id
        return room

    def set_state(self, code: str, state: str) -> Room | None:
        room = self._rooms.get(code)
        if room is None:
            return None
        room.state = state
        return room


class MemoryMatchStore:
    def __init__(self) -> None:
        self._matches: dict[str, Match] = {}
        self._by_room: dict[str, str] = {}

    def add(self, match: Match) -> None:
        self._matches[match.match_id] = match
        self._by_room[match.room_code] = match.match_id

    def get(self, match_id: str) -> Match | None:
        return self._matches.get(match_id)

    def get_by_room(self, room_code: str) -> Match | None:
        match_id = self._by_room.get(room_code)
        if match_id is None:
            return None
        return self._matches.get(match_id)

    def update(self, match: Match) -> None:
        self._matches[match.match_id] = match
        self._by_room[match.room_code] = match.match_id


class MemoryTurnStore:
    def __init__(self) -> None:
        self._turns: dict[str, Turn] = {}

    def add(self, turn: Turn) -> None:
        self._turns[turn.turn_id] = turn

    def get(self, turn_id: str) -> Turn | None:
        return self._turns.get(turn_id)

    def update(self, turn: Turn) -> None:
        self._turns[turn.turn_id] = turn