"""Pytest fixtures for backend testing."""

import os
import pytest
import fakeredis.aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.config import settings
from backend.app.db import Base, get_db
from backend.app.main import app
import backend.app.services.ratelimit as ratelimit_module

# Test in-memory SQLite database
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_TOKEN", "test_bearer_token")
    monkeypatch.setattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "100200300")
    monkeypatch.setattr(settings, "WHATSAPP_VERIFY_TOKEN", "verify_secret_token")
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", "super_secret_meta_app_key")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "test_anthropic_key")


@pytest.fixture
def fake_redis(monkeypatch):
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(ratelimit_module, "_redis_client", client)
    return client


@pytest.fixture
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_client(db_session, fake_redis):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
