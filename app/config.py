"""Configuration settings for the WhatsApp AI Agent."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # WhatsApp Cloud API credentials
    WHATSAPP_TOKEN: str = Field(default="", description="WhatsApp Cloud API Bearer Access Token")
    WHATSAPP_PHONE_NUMBER_ID: str = Field(default="", description="WhatsApp Business Phone Number ID")
    WHATSAPP_VERIFY_TOKEN: str = Field(default="", description="Custom verification token for webhook subscription")
    WHATSAPP_APP_SECRET: str = Field(default="", description="Meta App Secret for HMAC-SHA256 signature verification")

    # Meta Graph API Base Configuration
    GRAPH_API_VERSION: str = Field(default="v21.0", description="Meta Graph API Version")
    GRAPH_API_BASE_URL: str = Field(default="https://graph.facebook.com", description="Graph API Base URL")

    # Anthropic / Claude configuration
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API Key")
    CLAUDE_MODEL: str = Field(default="claude-3-5-sonnet-latest", description="Anthropic Claude model")
    MAX_TOOL_ITERATIONS: int = Field(default=8, description="Maximum iterations of tool-use loops per message")

    # Redis configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

    # Safety, Rate Limiting & Conversation Policy
    MAX_HISTORY_TURNS: int = Field(default=20, description="Max conversation turns preserved in context")
    RATE_LIMIT_PER_MIN: int = Field(default=10, description="Maximum messages allowed per minute per user")
    MAX_MESSAGE_LENGTH: int = Field(default=4096, description="WhatsApp max text character limit per message")

    # Human Handoff & Opt-Out Keywords
    HUMAN_HANDOFF_KEYWORDS: List[str] = Field(
        default=["agent", "human", "support", "representative", "helpdesk"],
        description="Keywords to trigger human agent handoff"
    )
    OPT_OUT_KEYWORDS: List[str] = Field(
        default=["stop", "unsubscribe", "cancel", "opt out", "optout"],
        description="Keywords honoring user opt-out per WhatsApp policy"
    )
    OPT_IN_KEYWORDS: List[str] = Field(
        default=["start", "unstop", "subscribe"],
        description="Keywords to opt back in"
    )


settings = Settings()
