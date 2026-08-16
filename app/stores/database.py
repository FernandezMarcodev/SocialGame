"""Persistencia en PostgreSQL (AD-002 / AD-003).

Implementa los mismos contratos que los stores en memoria pero respaldados por
PostgreSQL mediante SQLAlchemy (modo síncrono). Las entidades anidadas
(``players``, ``turn_order``, ``scores``, ``votes``) se serializan en columnas
``JSONB`` para conservar la forma exacta del dominio sin tablas relacionales
extra. Los stores reciben la entidad de dominio y devuelven entidades de
dominio, por lo que los servicios no necesitan conocer la capa de datos.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import BigInteger, Boolean, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, mapped_column, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB

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


def _normalize_url(url: str) -> str:
    """Render entrega ``postgres://`` pero los drivers esperan ``postgresql://``."""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


# --------------------------------------------------------------------------- #
# Conversión de entidades anidadas
# --------------------------------------------------------------------------- #


def _player_to_dict(p: PlayerRef) -> dict:
    return {
        "id": p.id,
        "username": p.username,
        "joined_at": p.joined_at,
        "profile_image_url": p.profile_image_url,
    }


def _dict_to_player(d: dict) -> PlayerRef:
    return PlayerRef(
        id=d["id"],
        username=d["username"],
        joined_at=d["joined_at"],
        profile_image_url=d.get("profile_image_url", ""),
    )


def _vote_to_dict(v: Vote) -> dict:
    return {"voter_id": v.voter_id, "value": v.value}


def _dict_to_vote(d: dict) -> Vote:
    return Vote(voter_id=d["voter_id"], value=d["value"])


# --------------------------------------------------------------------------- #
# Modelos ORM
# --------------------------------------------------------------------------- #


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id = mapped_column(String, primary_key=True)
    username = mapped_column(String, unique=True, nullable=False, index=True)
    email = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash = mapped_column(String, nullable=False)
    verified = mapped_column(Boolean, default=False)
    profile_image_url = mapped_column(String, default="")
    created_at = mapped_column(BigInteger, default=0)
    failed_attempts = mapped_column(Integer, default=0)
    blocked_until = mapped_column(BigInteger, nullable=True)

    @classmethod
    def from_entity(cls, u: User) -> "UserModel":
        return cls(
            id=u.id,
            username=u.username,
            email=u.email,
            password_hash=u.password_hash,
            verified=u.verified,
            profile_image_url=u.profile_image_url,
            created_at=u.created_at,
            failed_attempts=u.failed_attempts,
            blocked_until=u.blocked_until,
        )

    def to_entity(self) -> User:
        return User(
            id=self.id,
            username=self.username,
            email=self.email,
            password_hash=self.password_hash,
            verified=self.verified,
            profile_image_url=self.profile_image_url,
            created_at=self.created_at,
            failed_attempts=self.failed_attempts,
            blocked_until=self.blocked_until,
        )


class SessionModel(Base):
    __tablename__ = "sessions"

    token_hash = mapped_column(String, primary_key=True)
    user_id = mapped_column(String, nullable=False, index=True)
    created_at = mapped_column(BigInteger, default=0)
    expires_at = mapped_column(BigInteger, nullable=False)
    revoked = mapped_column(Boolean, default=False)

    @classmethod
    def from_entity(cls, s: Session) -> "SessionModel":
        return cls(
            token_hash=s.token_hash,
            user_id=s.user_id,
            created_at=s.created_at,
            expires_at=s.expires_at,
            revoked=s.revoked,
        )

    def to_entity(self) -> Session:
        return Session(
            token_hash=self.token_hash,
            user_id=self.user_id,
            created_at=self.created_at,
            expires_at=self.expires_at,
            revoked=self.revoked,
        )


class VerificationModel(Base):
    __tablename__ = "verification_tokens"

    token_hash = mapped_column(String, primary_key=True)
    user_id = mapped_column(String, nullable=False, index=True)
    kind = mapped_column(String, nullable=False)
    expires_at = mapped_column(BigInteger, nullable=False)
    used = mapped_column(Boolean, default=False)

    @classmethod
    def from_entity(cls, v: VerificationToken) -> "VerificationModel":
        return cls(
            token_hash=v.token_hash,
            user_id=v.user_id,
            kind=v.kind,
            expires_at=v.expires_at,
            used=v.used,
        )

    def to_entity(self) -> VerificationToken:
        return VerificationToken(
            token_hash=self.token_hash,
            user_id=self.user_id,
            kind=self.kind,
            expires_at=self.expires_at,
            used=self.used,
        )


class RoomModel(Base):
    __tablename__ = "rooms"

    code = mapped_column(String, primary_key=True)
    creator_id = mapped_column(String, nullable=False)
    modality_id = mapped_column(Integer, nullable=False)
    state = mapped_column(String, nullable=False)
    players = mapped_column(JSONB, nullable=False, default=list)
    min_players = mapped_column(Integer, nullable=False)
    max_players = mapped_column(Integer, nullable=False)
    created_at = mapped_column(BigInteger, default=0)

    @classmethod
    def from_entity(cls, r: Room) -> "RoomModel":
        return cls(
            code=r.code,
            creator_id=r.creator_id,
            modality_id=r.modality_id,
            state=r.state,
            players=[_player_to_dict(p) for p in r.players],
            min_players=r.min_players,
            max_players=r.max_players,
            created_at=r.created_at,
        )

    def to_entity(self) -> Room:
        return Room(
            code=self.code,
            creator_id=self.creator_id,
            modality_id=self.modality_id,
            state=self.state,
            players=[_dict_to_player(p) for p in (self.players or [])],
            min_players=self.min_players,
            max_players=self.max_players,
            created_at=self.created_at,
        )


class MatchModel(Base):
    __tablename__ = "matches"

    match_id = mapped_column(String, primary_key=True)
    room_code = mapped_column(String, unique=True, nullable=False, index=True)
    modality_id = mapped_column(Integer, nullable=False)
    state = mapped_column(String, nullable=False)
    players = mapped_column(JSONB, nullable=False, default=list)
    turn_order = mapped_column(JSONB, nullable=False, default=list)
    turn_index = mapped_column(Integer, default=0)
    current_turn = mapped_column(String, nullable=True)
    scores = mapped_column(JSONB, nullable=False, default=dict)
    created_at = mapped_column(BigInteger, default=0)

    @classmethod
    def from_entity(cls, m: Match) -> "MatchModel":
        return cls(
            match_id=m.match_id,
            room_code=m.room_code,
            modality_id=m.modality_id,
            state=m.state,
            players=[_player_to_dict(p) for p in m.players],
            turn_order=list(m.turn_order),
            turn_index=m.turn_index,
            current_turn=m.current_turn,
            scores=dict(m.scores),
            created_at=m.created_at,
        )

    def to_entity(self) -> Match:
        return Match(
            match_id=self.match_id,
            room_code=self.room_code,
            modality_id=self.modality_id,
            state=self.state,
            players=[_dict_to_player(p) for p in (self.players or [])],
            turn_order=list(self.turn_order or []),
            turn_index=self.turn_index,
            current_turn=self.current_turn,
            scores=dict(self.scores or {}),
            created_at=self.created_at,
        )


class TurnModel(Base):
    __tablename__ = "turns"

    turn_id = mapped_column(String, primary_key=True)
    match_id = mapped_column(String, nullable=False, index=True)
    author_id = mapped_column(String, nullable=False)
    state = mapped_column(String, nullable=False)
    phrase = mapped_column(String, nullable=True)
    secret_score = mapped_column(Integer, nullable=True)
    created_at = mapped_column(BigInteger, default=0)
    expires_at = mapped_column(BigInteger, nullable=False)
    voting_ends_at = mapped_column(BigInteger, nullable=True)
    votes = mapped_column(JSONB, nullable=False, default=list)
    points = mapped_column(Integer, default=0)

    @classmethod
    def from_entity(cls, t: Turn) -> "TurnModel":
        return cls(
            turn_id=t.turn_id,
            match_id=t.match_id,
            author_id=t.author_id,
            state=t.state,
            phrase=t.phrase,
            secret_score=t.secret_score,
            created_at=t.created_at,
            expires_at=t.expires_at,
            voting_ends_at=t.voting_ends_at,
            votes=[_vote_to_dict(v) for v in t.votes],
            points=t.points,
        )

    def to_entity(self) -> Turn:
        return Turn(
            turn_id=self.turn_id,
            match_id=self.match_id,
            author_id=self.author_id,
            state=self.state,
            phrase=self.phrase,
            secret_score=self.secret_score,
            created_at=self.created_at,
            expires_at=self.expires_at,
            voting_ends_at=self.voting_ends_at,
            votes=[_dict_to_vote(v) for v in (self.votes or [])],
            points=self.points,
        )


# --------------------------------------------------------------------------- #
# Gestor de conexiones
# --------------------------------------------------------------------------- #


class Database:
    """Envuelve el engine y el sessionmaker de SQLAlchemy."""

    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(
            _normalize_url(database_url), pool_pre_ping=True, future=True
        )
        self._Session = sessionmaker(bind=self._engine, expire_on_commit=False, future=True)

    @contextmanager
    def session(self) -> Iterator["Session"]:  # noqa: F821
        s = self._Session()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()


# --------------------------------------------------------------------------- #
# Stores
# --------------------------------------------------------------------------- #


class DatabaseUserStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    def _save(self, model: UserModel) -> None:
        with self._db.session() as s:
            s.merge(model)

    def add(self, user: User) -> None:
        self._save(UserModel.from_entity(user))

    def update(self, user: User) -> None:
        self._save(UserModel.from_entity(user))

    def get_by_id(self, user_id: str) -> Optional[User]:
        with self._db.session() as s:
            m = s.get(UserModel, user_id)
            return m.to_entity() if m else None

    def get_by_username(self, username: str) -> Optional[User]:
        with self._db.session() as s:
            m = s.scalars(select(UserModel).where(UserModel.username == username)).first()
            return m.to_entity() if m else None

    def get_by_email(self, email: str) -> Optional[User]:
        with self._db.session() as s:
            m = s.scalars(select(UserModel).where(UserModel.email == email)).first()
            return m.to_entity() if m else None


class DatabaseSessionStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    def _save(self, model: SessionModel) -> None:
        with self._db.session() as s:
            s.merge(model)

    def add(self, session: Session) -> None:
        self._save(SessionModel.from_entity(session))

    def get(self, token_hash: str) -> Optional[Session]:
        with self._db.session() as s:
            m = s.get(SessionModel, token_hash)
            return m.to_entity() if m else None

    def revoke(self, token_hash: str) -> None:
        with self._db.session() as s:
            m = s.get(SessionModel, token_hash)
            if m is not None:
                m.revoked = True


class DatabaseVerificationStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    def _save(self, model: VerificationModel) -> None:
        with self._db.session() as s:
            s.merge(model)

    def add(self, token: VerificationToken) -> None:
        self._save(VerificationModel.from_entity(token))

    def get(self, token_hash: str) -> Optional[VerificationToken]:
        with self._db.session() as s:
            m = s.get(VerificationModel, token_hash)
            return m.to_entity() if m else None

    def mark_used(self, token_hash: str) -> None:
        with self._db.session() as s:
            m = s.get(VerificationModel, token_hash)
            if m is not None:
                m.used = True


class DatabaseRoomStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    def _save(self, model: RoomModel) -> None:
        with self._db.session() as s:
            s.merge(model)

    def add(self, room: Room) -> None:
        self._save(RoomModel.from_entity(room))

    def get(self, code: str) -> Optional[Room]:
        with self._db.session() as s:
            m = s.get(RoomModel, code)
            return m.to_entity() if m else None

    def remove(self, code: str) -> None:
        with self._db.session() as s:
            m = s.get(RoomModel, code)
            if m is not None:
                s.delete(m)

    def get_room_by_player(self, user_id: str) -> Optional[Room]:
        with self._db.session() as s:
            stmt = select(RoomModel).where(
                RoomModel.players.contains([{"id": user_id}])
            )
            m = s.scalars(stmt).first()
            return m.to_entity() if m else None

    def add_player(self, code: str, player: PlayerRef) -> Optional[Room]:
        with self._db.session() as s:
            m = s.get(RoomModel, code)
            if m is None:
                return None
            players = list(m.players or [])
            players.append(_player_to_dict(player))
            m.players = players
            s.merge(m)
            return RoomModel.to_entity(m)

    def remove_player(self, code: str, player_id: str) -> Optional[Room]:
        with self._db.session() as s:
            m = s.get(RoomModel, code)
            if m is None:
                return None
            players = [p for p in (m.players or []) if p.get("id") != player_id]
            m.players = players
            s.merge(m)
            return RoomModel.to_entity(m)

    def set_creator(self, code: str, creator_id: str) -> Optional[Room]:
        with self._db.session() as s:
            m = s.get(RoomModel, code)
            if m is None:
                return None
            m.creator_id = creator_id
            s.merge(m)
            return RoomModel.to_entity(m)

    def set_state(self, code: str, state: str) -> Optional[Room]:
        with self._db.session() as s:
            m = s.get(RoomModel, code)
            if m is None:
                return None
            m.state = state
            s.merge(m)
            return RoomModel.to_entity(m)


class DatabaseMatchStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    def _save(self, model: MatchModel) -> None:
        with self._db.session() as s:
            s.merge(model)

    def add(self, match: Match) -> None:
        self._save(MatchModel.from_entity(match))

    def update(self, match: Match) -> None:
        self._save(MatchModel.from_entity(match))

    def get(self, match_id: str) -> Optional[Match]:
        with self._db.session() as s:
            m = s.get(MatchModel, match_id)
            return m.to_entity() if m else None

    def get_by_room(self, room_code: str) -> Optional[Match]:
        with self._db.session() as s:
            m = s.scalars(
                select(MatchModel).where(MatchModel.room_code == room_code)
            ).first()
            return m.to_entity() if m else None


class DatabaseTurnStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    def _save(self, model: TurnModel) -> None:
        with self._db.session() as s:
            s.merge(model)

    def add(self, turn: Turn) -> None:
        self._save(TurnModel.from_entity(turn))

    def update(self, turn: Turn) -> None:
        self._save(TurnModel.from_entity(turn))

    def get(self, turn_id: str) -> Optional[Turn]:
        with self._db.session() as s:
            m = s.get(TurnModel, turn_id)
            return m.to_entity() if m else None
