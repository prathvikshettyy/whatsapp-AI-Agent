from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class ToolCallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    args_redacted: Optional[Dict[str, Any]] = None
    status: str
    latency_ms: int
    created_at: datetime


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    media_type: Optional[str] = None
    media_ref: Optional[str] = None
    created_at: datetime
    tool_calls: Optional[List[ToolCallResponse]] = []


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    contact_id: str
    wa_id_masked: str
    wa_id_full: Optional[str] = None
    name: Optional[str] = None
    status: str
    last_message_preview: str
    last_user_msg_at: datetime
    unread: int = 0


class SendMessageRequest(BaseModel):
    content: str
