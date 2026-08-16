import pytest

from app.api.errors import ApiError
from app.core.config import Settings
from app.core.security import PasswordHasherArgon2, hash_token
from app.domain.entities import User
from app.email.provider import ConsoleEmailProvider
from app.services.auth_service import AuthService
from app.stores.memory import MemorySessionStore, MemoryUserStore, MemoryVerificationStore

PASSWORD = "Passw0rd!"


class FakeClock:
    def __init__(self, start: int = 0) -> None:
        self._now = start

    def __call__(self) -> int:
        return self._now

    def advance(self, ms: int) -> None:
        self._now += ms


def build_auth(settings, clock):
    users = MemoryUserStore()
    sessions = MemorySessionStore()
    verifications = MemoryVerificationStore()
    emails = ConsoleEmailProvider()
    auth = AuthService(
        settings=settings,
        users=users,
        sessions=sessions,
        verifications=verifications,
        emails=emails,
        now=clock,
    )
    users.add(
        User(
            id="usr-test",
            username="ken",
            email="ken@example.com",
            password_hash=PasswordHasherArgon2().hash(PASSWORD),
            verified=True,
            created_at=clock(),
        )
    )
    return auth


def test_session_expires():
    settings = Settings(_env_file=None, token_ttl_seconds=1)
    clock = FakeClock(1000)
    auth = build_auth(settings, clock)
    result = auth.login("ken", PASSWORD)
    clock.advance(2000)
    with pytest.raises(ApiError) as exc:
        auth.resolve_access_token(result.access_token)
    assert exc.value.code == "TOKEN_EXPIRED"


def test_lockout_expires_and_allows_login_again():
    settings = Settings(_env_file=None, max_login_attempts=2, lockout_seconds=5)
    clock = FakeClock(1000)
    auth = build_auth(settings, clock)
    with pytest.raises(ApiError):
        auth.login("ken", "mal")
    with pytest.raises(ApiError) as exc:
        auth.login("ken", "mal")
    assert exc.value.code == "ACCOUNT_BLOCKED"
    clock.advance(6000)
    result = auth.login("ken", PASSWORD)
    assert result.access_token


def test_hash_token_is_safe_to_store():
    token = "valor-opaco"
    assert hash_token(token) != token
    assert len(hash_token(token)) == 64