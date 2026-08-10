import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def outbox():
    return []


@pytest.fixture
def settings():
    return Settings(_env_file=None, debug=True)


@pytest.fixture
def app(settings, outbox):
    return create_app(settings=settings, outbox=outbox)


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client