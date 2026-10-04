"""Audit log model for staff actions."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, JSON, String

from backend.app.db import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id = Column(String(36), ForeignKey("staff_users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)  # 'takeover', 'release', 'settings_update', 'kb_edit'
    target = Column(String(255), nullable=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
