"""Conversation model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from backend.app.db import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contact_id = Column(String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="bot", nullable=False)  # 'bot', 'human', 'closed'
    last_user_msg_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    assigned_to = Column(String(36), ForeignKey("staff_users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    contact = relationship("Contact", back_populates="conversations")
    assigned_staff = relationship("StaffUser", foreign_keys=[assigned_to])
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

    __table_args__ = (
        Index("idx_conversations_status_last_msg", "status", "last_user_msg_at"),
    )
