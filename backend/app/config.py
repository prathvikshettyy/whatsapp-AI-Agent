"""Backend configuration using pydantic-settings."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database & Redis
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./whatsapp_agent.db",
        description="Async PostgreSQL or SQLite connection string"
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for cache, ratelimiting, and arq queue"
    )

    # WhatsApp Business Cloud API
    WHATSAPP_TOKEN: str = Field(default="", description="WhatsApp Permanent Bearer Token")
    WHATSAPP_PHONE_NUMBER_ID: str = Field(default="", description="Meta Phone Number ID")
    WHATSAPP_VERIFY_TOKEN: str = Field(default="test_verify_token", description="Webhook verify token")
    WHATSAPP_APP_SECRET: str = Field(default="", description="Meta App Secret for HMAC verification")
    GRAPH_API_VERSION: str = Field(default="v21.0", description="Meta Graph API Version")
    GRAPH_API_BASE_URL: str = Field(default="https://graph.facebook.com", description="Graph API Base URL")

    # Anthropic Claude
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API Key")
    CLAUDE_MODEL: str = Field(default="claude-3-5-sonnet-latest", description="Claude Model Name")
    MAX_STEPS: int = Field(default=8, description="Max tool-use reasoning steps per turn")

    # Security & JWT
    JWT_SECRET: str = Field(default="super_secret_jwt_signing_key_change_me", description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=10080, description="Session expiry in minutes (7 days)")

    # Operational & Safety Controls
    RATE_LIMIT_PER_MIN: int = Field(default=10, description="Rate limit per user per minute")
    MAX_HISTORY_TURNS: int = Field(default=20, description="Max conversation turns in context window")
    DAILY_TOKEN_BUDGET: int = Field(default=500000, description="Daily token budget limit before alerting")

    # Compliance & Handoff Keywords
    HANDOFF_KEYWORDS: List[str] = Field(
        default=["agent", "human", "support", "representative", "helpdesk"],
        description="Keywords triggering human handoff"
    )
    OPT_OUT_KEYWORDS: List[str] = Field(
        default=["stop", "unsubscribe", "cancel", "opt out"],
        description="WhatsApp opt-out keywords"
    )
    OPT_IN_KEYWORDS: List[str] = Field(
        default=["start", "unstop", "subscribe"],
        description="WhatsApp opt-in keywords"
    )


settings = Settings()
