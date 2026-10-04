"""Knowledge base documents model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String, Text

from backend.app.db import Base


class KbDoc(Base):
    __tablename__ = "kb_docs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
