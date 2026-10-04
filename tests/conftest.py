"""Pytest fixtures and test environment configuration."""

import os
import pytest
import fakeredis.aioredis
from app.config import settings
from app.store import RedisStore


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set test credentials and mock environment variables."""
    monkeypatch.setattr(settings, "WHATSAPP_TOKEN", "mock_whatsapp_bearer_token")
    monkeypatch.setattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "1000999888")
    monkeypatch.setattr(settings, "WHATSAPP_VERIFY_TOKEN", "secret_verify_token_123")
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", "super_secret_meta_app_key")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "mock_anthropic_api_key")
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MIN", 5)


@pytest.fixture
def fake_redis():
    """Create an isolated fake Redis client for async testing."""
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def fake_store(fake_redis):
    """Create a RedisStore instance using fake_redis."""
    return RedisStore(redis_client=fake_redis)
