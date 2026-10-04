"""Contact model representing WhatsApp users."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship

from backend.app.db import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wa_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    opted_out = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    conversations = relationship("Conversation", back_populates="contact", cascade="all, delete-orphan")
