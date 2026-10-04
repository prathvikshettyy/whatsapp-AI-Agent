"""Admin API routes for the staff dashboard."""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.store import store
from app.whatsapp import mask_phone_number, whatsapp_client

admin_router = APIRouter()

# In-memory storage for admin KB & prompt versions (can be stored in Redis or DB)
MOCK_KB_STORE: List[Dict[str, Any]] = [
    {
        "id": "kb_1",
        "title": "Operating Hours & Customer Support",
        "key": "hours",
        "content": "Our customer support team is available Monday through Friday from 9:00 AM to 6:00 PM EST. Automated bot support runs 24/7.",
        "tags": ["general", "support", "hours"],
        "updated_at": "2026-09-15T10:00:00Z",
    },
    {
        "id": "kb_2",
        "title": "Return and Exchange Policy",
        "key": "return",
        "content": "We offer a 30-day return policy for unused items in original packaging. Refunds are processed to original payment method within 3-5 business days of receipt.",
        "tags": ["returns", "policy", "refunds"],
        "updated_at": "2026-09-20T14:30:00Z",
    },
]

MOCK_PROMPT_HISTORY: List[Dict[str, Any]] = [
    {
        "id": "v3",
        "created_at": "2026-10-02T16:00:00Z",
        "created_by": "Sarah Jenkins",
        "summary": "Add strict confirmation rule for refunds & cancellations",
        "prompt": "You are a customer support bot on WhatsApp...",
    }
]

# Request models
class LoginRequest(BaseModel):
    email: str
    password: Optional[str] = None

class SendMessageRequest(BaseModel):
    content: str

class SettingsUpdateRequest(BaseModel):
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    rate_limit_per_min: Optional[int] = None
    max_history_turns: Optional[int] = None
    handoff_keywords: Optional[List[str]] = None
    opt_out_keywords: Optional[List[str]] = None
    version_summary: Optional[str] = None


@admin_router.post("/auth/login")
async def login(req: LoginRequest, response: Response):
    role = "agent" if "agent" in req.email.lower() else "admin"
    user = {
        "id": "usr_staff_1",
        "email": req.email,
        "name": "Sarah Jenkins" if role == "admin" else "Alex Support",
        "role": role,
    }
    # Set httpOnly session cookie
    response.set_cookie(
        key="staff_session",
        value=req.email,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7,
    )
    return {"success": True, "user": user}


@admin_router.get("/auth/me")
async def get_current_user(staff_session: Optional[str] = Cookie(None)):
    email = staff_session or "admin@company.com"
    role = "agent" if "agent" in email.lower() else "admin"
    return {
        "id": "usr_staff_1",
        "email": email,
        "name": "Sarah Jenkins" if role == "admin" else "Alex Support",
        "role": role,
    }


@admin_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("staff_session")
    return {"success": True}


@admin_router.get("/conversations")
async def list_conversations():
    # Retrieve active conversations from store or provide standard demo set
    return {
        "items": [
            {
                "id": "conv_1",
                "wa_id_masked": "+1 (555) ••••• 8921",
                "wa_id_full": "+15552348921",
                "name": "Alex Morgan",
                "status": "human",
                "last_message_preview": "Can I talk to a real person? My package is missing.",
                "last_user_msg_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 900)),
                "unread": 2,
            },
            {
                "id": "conv_2",
                "wa_id_masked": "+44 (791) ••••• 4310",
                "wa_id_full": "+447911124310",
                "name": "Marcus Vance",
                "status": "bot",
                "last_message_preview": "Your order *ORD-1029* is currently *In Transit* with FedEx.",
                "last_user_msg_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 7200)),
                "unread": 0,
            },
        ],
        "next_cursor": None,
    }


@admin_router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str):
    history = await store.get_history(conversation_id, max_turns=50)
    messages = []
    now = time.time()
    for idx, item in enumerate(history):
        messages.append({
            "id": f"msg_{idx}",
            "conversation_id": conversation_id,
            "role": item.get("role", "user"),
            "content": item.get("content", ""),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - (len(history) - idx) * 60)),
        })
    return {"items": messages, "next_cursor": None}


@admin_router.post("/conversations/{conversation_id}/takeover")
async def takeover_conversation(conversation_id: str):
    await store.set_handoff(conversation_id, True)
    return {"status": "human", "success": True}


@admin_router.post("/conversations/{conversation_id}/release")
async def release_conversation(conversation_id: str):
    await store.set_handoff(conversation_id, False)
    return {"status": "bot", "success": True}


@admin_router.post("/conversations/{conversation_id}/send")
async def send_staff_message(conversation_id: str, req: SendMessageRequest):
    # Send via WhatsApp Cloud API
    try:
        await whatsapp_client.send_text_message(to=conversation_id, text=req.content)
    except Exception:
        # Best effort in development
        pass

    await store.add_turn(conversation_id, role="staff", content=req.content)
    return {
        "id": f"staff_{int(time.time()*1000)}",
        "conversation_id": conversation_id,
        "role": "staff",
        "content": req.content,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@admin_router.get("/stream")
async def sse_event_stream(request: Request):
    """Server-Sent Events (SSE) stream for live chat updates and handoff alerts."""
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            # Send heartbeat keepalive ping every 15s per specification
            yield f": ping - {time.time()}\n\n"
            await asyncio.sleep(15)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@admin_router.get("/settings")
async def get_settings():
    return {
        "system_prompt": "You are a customer support AI agent on WhatsApp...",
        "model": settings.CLAUDE_MODEL,
        "rate_limit_per_min": settings.RATE_LIMIT_PER_MIN,
        "max_history_turns": settings.MAX_HISTORY_TURNS,
        "handoff_keywords": settings.HUMAN_HANDOFF_KEYWORDS,
        "opt_out_keywords": settings.OPT_OUT_KEYWORDS,
    }


@admin_router.put("/settings")
async def update_settings(req: SettingsUpdateRequest):
    if req.model:
        settings.CLAUDE_MODEL = req.model
    if req.rate_limit_per_min:
        settings.RATE_LIMIT_PER_MIN = req.rate_limit_per_min
    if req.max_history_turns:
        settings.MAX_HISTORY_TURNS = req.max_history_turns
    return {"status": "success"}


@admin_router.get("/settings/prompt-history")
async def get_prompt_history():
    return MOCK_PROMPT_HISTORY


@admin_router.get("/kb")
async def list_kb():
    return MOCK_KB_STORE


@admin_router.post("/kb")
async def create_kb(article: Dict[str, Any]):
    new_art = {
        "id": f"kb_{len(MOCK_KB_STORE)+1}",
        "title": article.get("title", "Untitled"),
        "key": article.get("key", "faq_key"),
        "content": article.get("content", ""),
        "tags": article.get("tags", []),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    MOCK_KB_STORE.append(new_art)
    return new_art
