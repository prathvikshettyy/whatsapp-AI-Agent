"""System settings & prompt versioning model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text

from backend.app.db import Base


class Setting(Base):
    __tablename__ = "settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    system_prompt = Column(Text, nullable=False)
    model = Column(String(64), default="claude-3-5-sonnet-latest", nullable=False)
    rate_limit_per_min = Column(Integer, default=10, nullable=False)
    handoff_keyword = Column(String(255), default="agent", nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(String(255), default="System", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
