"""Conversations API routes for staff admin dashboard."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db import get_db
from backend.app.models.audit_log import AuditLog
from backend.app.models.contact import Contact
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.models.tool_call import ToolCall
from backend.app.schemas.conversation import ConversationResponse, MessageResponse, SendMessageRequest
from backend.app.services.events import publish_event
from backend.app.services.whatsapp import mask_phone_number, whatsapp_service

conversations_router = APIRouter(prefix="/conversations", tags=["conversations"])


@conversations_router.get("")
async def list_conversations(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Conversation)
        .join(Contact, Conversation.contact_id == Contact.id)
        .options(selectinload(Conversation.contact), selectinload(Conversation.messages))
        .order_by(desc(Conversation.last_user_msg_at))
        .limit(limit)
    )

    if status_filter and status_filter != "all":
        query = query.where(Conversation.status == status_filter)

    res = await db.execute(query)
    conversations = res.scalars().all()

    items = []
    for c in conversations:
        last_msg = c.messages[-1].content if c.messages else "No messages"
        items.append({
            "id": c.id,
            "contact_id": c.contact_id,
            "wa_id_masked": mask_phone_number(c.contact.wa_id),
            "wa_id_full": c.contact.wa_id,
            "name": c.contact.name or f"User {c.contact.wa_id[-4:]}",
            "status": c.status,
            "last_message_preview": last_msg,
            "last_user_msg_at": c.last_user_msg_at,
            "unread": 0,
        })

    return {"items": items, "next_cursor": None}


@conversations_router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .options(selectinload(Message.tool_calls))
        .order_by(Message.created_at.asc())
    )
    res = await db.execute(stmt)
    messages = res.scalars().all()

    result = []
    for m in messages:
        result.append({
            "id": m.id,
            "conversation_id": m.conversation_id,
            "role": m.role,
            "content": m.content,
            "media_type": m.media_type,
            "media_ref": m.media_ref,
            "created_at": m.created_at,
            "tool_calls": [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "args_redacted": tc.args_redacted,
                    "status": tc.status,
                    "latency_ms": tc.latency_ms,
                    "created_at": tc.created_at,
                }
                for tc in m.tool_calls
            ],
        })

    return {"items": result, "next_cursor": None}


@conversations_router.post("/{conversation_id}/takeover")
async def takeover(conversation_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.status = "human"
    db.add(AuditLog(action="takeover", target=conversation_id))
    await db.commit()

    await publish_event("conversation.updated", {"id": conversation_id, "status": "human"})
    return {"status": "human", "success": True}


@conversations_router.post("/{conversation_id}/release")
async def release(conversation_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.status = "bot"
    db.add(AuditLog(action="release", target=conversation_id))
    await db.commit()

    await publish_event("conversation.updated", {"id": conversation_id, "status": "bot"})
    return {"status": "bot", "success": True}


@conversations_router.post("/{conversation_id}/send")
async def send_staff_message(
    conversation_id: str,
    req: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.contact))
    )
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 24h Window enforcement check
    now = datetime.now(timezone.utc)
    last_msg_time = conv.last_user_msg_at
    if last_msg_time.tzinfo is None:
        last_msg_time = last_msg_time.replace(tzinfo=timezone.utc)
    diff_sec = (now - last_msg_time).total_seconds()
    if diff_sec > 86400:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="24-hour customer service window expired. Meta policy requires an approved template message."
        )

    # Save staff message in DB
    staff_msg = Message(
        conversation_id=conversation_id,
        role="staff",
        content=req.content,
    )
    db.add(staff_msg)
    await db.commit()
    await db.refresh(staff_msg)

    # Send message to user via WhatsApp
    try:
        await whatsapp_service.send_text(to=conv.contact.wa_id, body=req.content)
    except Exception as e:
        # Don't fail the API save if WhatsApp test credential is not set up
        pass

    # Publish live SSE event
    await publish_event("message.created", {
        "id": staff_msg.id,
        "conversation_id": conversation_id,
        "role": "staff",
        "content": req.content,
        "created_at": staff_msg.created_at.isoformat(),
    })

    return {
        "id": staff_msg.id,
        "conversation_id": conversation_id,
        "role": "staff",
        "content": staff_msg.content,
        "created_at": staff_msg.created_at,
    }
