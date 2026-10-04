"""Async background tasks executed by arq worker."""

from datetime import datetime, timezone
import json
import time
from typing import Any, Dict, Optional
from sqlalchemy import select
import structlog

from backend.app.config import settings
from backend.app.db import AsyncSessionLocal
from backend.app.models.contact import Contact
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.models.tool_call import ToolCall
from backend.app.services.agent import agent_service
from backend.app.services.events import publish_event
from backend.app.services.history import load_conversation_history
from backend.app.services.ratelimit import check_rate_limit, get_redis
from backend.app.services.whatsapp import mask_phone_number, whatsapp_service

logger = structlog.get_logger(__name__)


async def process_inbound(ctx: Dict[str, Any], message_payload: Dict[str, Any]) -> None:
    """
    Main background task:
    1. Upserts Contact and Conversation.
    2. Stores incoming Message.
    3. Checks gates: Rate limiting, Opt-out ("STOP"), Human Handoff ("AGENT").
    4. If status == 'human', stores message and skips bot reply.
    5. Executes Claude Agent loop with history and tools.
    6. Stores assistant reply and ToolCalls in Postgres.
    7. Sends reply to user via WhatsApp Cloud API.
    8. Publishes SSE event for real-time dashboard.
    """
    sender = message_payload.get("from")
    wa_msg_id = message_payload.get("id")
    msg_type = message_payload.get("type", "text")

    if not sender or not wa_msg_id:
        logger.warning("invalid_inbound_payload", payload=message_payload)
        return

    logger.info("processing_inbound_message", wa_msg_id=wa_msg_id, sender=mask_phone_number(sender))

    # Mark message as read
    await whatsapp_service.mark_read(wa_msg_id)

    # Extract text content
    user_text = ""
    if msg_type == "text":
        user_text = message_payload.get("text", {}).get("body", "").strip()
    elif msg_type == "image":
        user_text = message_payload.get("image", {}).get("caption", "[Image message]").strip()
    elif msg_type in ["audio", "voice"]:
        user_text = "[Voice Note received]"
    elif msg_type == "interactive":
        interactive = message_payload.get("interactive", {})
        user_text = interactive.get("button_reply", {}).get("title", "")

    cleaned = user_text.lower().strip()

    # DB session
    async with AsyncSessionLocal() as session:
        # 1. Upsert Contact
        stmt = select(Contact).where(Contact.wa_id == sender)
        contact = (await session.execute(stmt)).scalar_one_or_none()
        if not contact:
            contact = Contact(wa_id=sender, name=f"User {sender[-4:]}")
            session.add(contact)
            await session.flush()

        # 2. Get or create Conversation
        stmt = (
            select(Conversation)
            .where(Conversation.contact_id == contact.id)
            .order_by(Conversation.created_at.desc())
        )
        conversation = (await session.execute(stmt)).scalars().first()
        now = datetime.now(timezone.utc)

        if not conversation or conversation.status == "closed":
            conversation = Conversation(contact_id=contact.id, status="bot", last_user_msg_at=now)
            session.add(conversation)
            await session.flush()
        else:
            conversation.last_user_msg_at = now

        # 3. Store incoming user message
        inbound_msg = Message(
            wa_msg_id=wa_msg_id,
            conversation_id=conversation.id,
            role="user",
            content=user_text,
            media_type=msg_type if msg_type != "text" else None,
        )
        session.add(inbound_msg)
        await session.flush()

        # Publish live message event to dashboard
        await publish_event("message.created", {
            "id": inbound_msg.id,
            "conversation_id": conversation.id,
            "role": "user",
            "content": user_text,
            "created_at": inbound_msg.created_at.isoformat(),
        })

        # --- GATE 1: Rate Limiting ---
        within_limit = await check_rate_limit(sender, limit=settings.RATE_LIMIT_PER_MIN, window=60)
        if not within_limit:
            logger.warning("rate_limit_exceeded", sender=mask_phone_number(sender))
            await whatsapp_service.send_text(
                to=sender,
                body="*Notice*: You are sending messages too quickly. Please wait a moment before sending another message.",
                reply_to_message_id=wa_msg_id,
            )
            await session.commit()
            return

        # --- GATE 2: Opt-Out Policy ("STOP") ---
        if cleaned in settings.OPT_OUT_KEYWORDS:
            contact.opted_out = True
            await session.commit()
            await whatsapp_service.send_text(
                to=sender,
                body="You have been unsubscribed from automated messages. Reply *START* anytime to resubscribe.",
                reply_to_message_id=wa_msg_id,
            )
            return

        # --- GATE 3: Opt-In Policy ("START") ---
        if contact.opted_out:
            if cleaned in settings.OPT_IN_KEYWORDS:
                contact.opted_out = False
                await session.commit()
                await whatsapp_service.send_text(
                    to=sender,
                    body="Welcome back! You have resubscribed to automated messages. How can I help you today?",
                    reply_to_message_id=wa_msg_id,
                )
            return

        # --- GATE 4: Human Handoff ("AGENT") ---
        if cleaned in settings.HANDOFF_KEYWORDS:
            conversation.status = "human"
            await session.commit()
            await publish_event("handoff.requested", {
                "id": conversation.id,
                "name": contact.name,
                "wa_id_masked": mask_phone_number(sender),
                "last_message_preview": user_text,
            })
            await whatsapp_service.send_text(
                to=sender,
                body=(
                    "I have flagged this conversation for a *human support agent*. "
                    "A team member will follow up shortly.\n\n"
                    "_Tip: Send *BOT* anytime to switch back to the AI assistant._"
                ),
                reply_to_message_id=wa_msg_id,
            )
            return

        # If currently assigned to human, do not send bot response
        if conversation.status == "human":
            if cleaned in ["bot", "resume", "restart"]:
                conversation.status = "bot"
                await session.commit()
                await whatsapp_service.send_text(
                    to=sender,
                    body="Welcome back to the AI assistant! How can I assist you right now?",
                    reply_to_message_id=wa_msg_id,
                )
            else:
                logger.info("conversation_in_human_mode_skipping_bot", conversation_id=conversation.id)
                await session.commit()
            return

        # --- Check pending action confirmation ---
        redis_client = await get_redis()
        pending_key = f"wa:pending_confirmation:{sender}"
        pending_val = await redis_client.get(pending_key)
        is_confirmed = False
        if pending_val:
            if cleaned in ["yes", "confirm", "proceed", "sure", "ok"]:
                is_confirmed = True
                await redis_client.delete(pending_key)
            elif cleaned in ["no", "cancel", "stop", "abort"]:
                await redis_client.delete(pending_key)
                await whatsapp_service.send_text(
                    to=sender,
                    body="The action has been canceled. Is there anything else I can help you with?",
                    reply_to_message_id=wa_msg_id,
                )
                await session.commit()
                return

        # --- Load history & run Claude agent ---
        history = await load_conversation_history(session, conversation.id, settings.MAX_HISTORY_TURNS)
        history.append({"role": "user", "content": user_text})

        reply_text, tool_audits, tokens_in, tokens_out = await agent_service.run(
            messages=history,
            wa_id=sender,
            is_confirmed=is_confirmed,
        )

        # 4. Save outbound bot reply & tool calls
        bot_msg = Message(
            conversation_id=conversation.id,
            role="bot",
            content=reply_text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )
        session.add(bot_msg)
        await session.flush()

        for audit in tool_audits:
            tool_record = ToolCall(
                message_id=bot_msg.id,
                name=audit["name"],
                args_redacted=audit["args"],
                status=audit["status"],
                latency_ms=audit["latency_ms"],
            )
            session.add(tool_record)
            if audit["status"] == "requires_user_confirmation":
                await redis_client.set(pending_key, json.dumps(audit["args"]), ex=600)

        await session.commit()

        # 5. Send reply via WhatsApp Cloud API
        send_resps = await whatsapp_service.send_text(
            to=sender,
            body=reply_text,
            reply_to_message_id=wa_msg_id,
        )
        if send_resps and "messages" in send_resps[0]:
            bot_msg.wa_msg_id = send_resps[0]["messages"][0]["id"]
            await session.commit()

        # 6. Publish SSE event
        await publish_event("message.created", {
            "id": bot_msg.id,
            "conversation_id": conversation.id,
            "role": "bot",
            "content": reply_text,
            "created_at": bot_msg.created_at.isoformat(),
        })
