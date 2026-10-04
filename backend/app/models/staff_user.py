"""Staff users and RBAC model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String

from backend.app.db import Base


class StaffUser(Base):
    __tablename__ = "staff_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="agent", nullable=False)  # 'admin', 'agent'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
