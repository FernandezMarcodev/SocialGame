"""Implementaciones en memoria de los stores.

Mientras no exista persistencia (feature de PostgreSQL), la API usa almacenes
en memoria por proceso, coherente con AD-002/AD-003.
"""

from app.domain.entities import Session, User, VerificationToken


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