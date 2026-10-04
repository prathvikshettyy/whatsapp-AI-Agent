"""Async message processing worker.

Handles rate limiting, opt-out / opt-in compliance, human handoff routing,
media retrieval, confirmation flows, Claude agent reasoning, and WhatsApp message dispatch.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional
import redis.asyncio as aioredis

from app.agent import WhatsAppAgent, agent as default_agent
from app.config import settings
from app.store import RedisStore, store as default_store
from app.whatsapp import WhatsAppClient, mask_phone_number, whatsapp_client as default_whatsapp

logger = logging.getLogger(__name__)

REDIS_QUEUE_KEY = "wa:incoming_messages_queue"


async def enqueue_message(message_payload: Dict[str, Any], redis_client: Optional[aioredis.Redis] = None) -> None:
    """Push incoming WhatsApp message payload to Redis queue for worker processing."""
    client = redis_client or (await default_store.get_client())
    await client.lpush(REDIS_QUEUE_KEY, json.dumps(message_payload))


async def process_message(
    message: Dict[str, Any],
    store: Optional[RedisStore] = None,
    whatsapp: Optional[WhatsAppClient] = None,
    agent: Optional[WhatsAppAgent] = None,
) -> None:
    """
    Process an individual WhatsApp message according to all business and safety rules.
    """
    store = store or default_store
    whatsapp = whatsapp or default_whatsapp
    agent = agent or default_agent

    sender = message.get("from")
    message_id = message.get("id")
    msg_type = message.get("type", "unknown")

    if not sender or not message_id:
        logger.warning("Invalid message received missing sender or message_id")
        return

    logger.info(
        f"Processing message {message_id} of type '{msg_type}' from {mask_phone_number(sender)}"
    )

    # 1. Mark incoming message as read
    await whatsapp.mark_as_read(message_id)

    # 2. Check rate limit
    is_allowed = await store.check_rate_limit(
        wa_id=sender,
        limit=settings.RATE_LIMIT_PER_MIN,
        window=60,
    )
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for {mask_phone_number(sender)}")
        await whatsapp.send_text_message(
            to=sender,
            text="*Notice*: You are sending messages too quickly. Please wait a moment before sending another message.",
            reply_to_message_id=message_id,
        )
        return

    # Extract text content if present
    user_text = ""
    if msg_type == "text":
        user_text = message.get("text", {}).get("body", "").strip()
    elif msg_type == "interactive":
        # Handle button or list reply
        interactive = message.get("interactive", {})
        if "button_reply" in interactive:
            user_text = interactive["button_reply"].get("title", "")
        elif "list_reply" in interactive:
            user_text = interactive["list_reply"].get("title", "")
    elif msg_type == "image":
        user_text = message.get("image", {}).get("caption", "").strip()

    cleaned_text = user_text.lower().strip()

    # 3. Check WhatsApp Opt-Out policy ("stop", "unsubscribe", etc.)
    if cleaned_text in settings.OPT_OUT_KEYWORDS:
        await store.set_opt_out(sender, True)
        logger.info(f"User {mask_phone_number(sender)} opted out")
        await whatsapp.send_text_message(
            to=sender,
            text="You have been unsubscribed from automated messages. Reply *START* anytime to resubscribe.",
            reply_to_message_id=message_id,
        )
        return

    # 4. Check Opt-In ("start", "unstop")
    is_opted_out = await store.is_opted_out(sender)
    if is_opted_out:
        if cleaned_text in settings.OPT_IN_KEYWORDS:
            await store.set_opt_out(sender, False)
            logger.info(f"User {mask_phone_number(sender)} opted back in")
            await whatsapp.send_text_message(
                to=sender,
                text="Welcome back! You have resubscribed to automated messages. How can I help you today?",
                reply_to_message_id=message_id,
            )
            return
        else:
            # User opted out previously and did not say START -> do not reply
            logger.info(f"Ignoring message from opted-out user {mask_phone_number(sender)}")
            return

    # 5. Check Human Handoff ("agent", "human", "support")
    if cleaned_text in settings.HUMAN_HANDOFF_KEYWORDS:
        await store.set_handoff(sender, True)
        logger.info(f"User {mask_phone_number(sender)} requested human handoff")
        await whatsapp.send_text_message(
            to=sender,
            text=(
                "I have flagged this conversation for a *human support agent*. "
                "A team member will respond here shortly.\n\n"
                "_Tip: Send *BOT* anytime to switch back to the AI assistant._"
            ),
            reply_to_message_id=message_id,
        )
        return

    # If already handed off to human:
    is_handed_off = await store.is_handed_off(sender)
    if is_handed_off:
        if cleaned_text in ["bot", "resume", "restart"]:
            await store.set_handoff(sender, False)
            logger.info(f"User {mask_phone_number(sender)} resumed bot from human handoff")
            await whatsapp.send_text_message(
                to=sender,
                text="Welcome back to the AI assistant! How can I assist you right now?",
                reply_to_message_id=message_id,
            )
            return
        else:
            # Human agent handles this conversation, bot stays quiet
            logger.info(f"User {mask_phone_number(sender)} is in human handoff; skipping bot response")
            return

    # 6. Check confirmation for sensitive actions
    pending_action = await store.get_pending_action(sender)
    is_confirmed_action = False
    if pending_action:
        if cleaned_text in ["yes", "confirm", "proceed", "sure", "ok", "yes, please"]:
            is_confirmed_action = True
            await store.clear_pending_action(sender)
        elif cleaned_text in ["no", "cancel", "nevermind", "stop", "abort"]:
            await store.clear_pending_action(sender)
            await whatsapp.send_text_message(
                to=sender,
                text="The action has been canceled. Is there anything else I can help you with?",
                reply_to_message_id=message_id,
            )
            return

    # 7. Media Handling (Images, Audio, Voice)
    image_bytes: Optional[bytes] = None
    image_mime: Optional[str] = None

    if msg_type == "image":
        media_id = message.get("image", {}).get("id")
        if media_id:
            try:
                media_url, image_mime = await whatsapp.get_media_url(media_id)
                image_bytes = await whatsapp.download_media(media_url)
            except Exception as e:
                logger.error(f"Failed to fetch image media: {e}")
                await whatsapp.send_text_message(
                    to=sender,
                    text="I received your image but could not download it. Please try sending it again.",
                    reply_to_message_id=message_id,
                )
                return

    elif msg_type in ["audio", "voice"]:
        user_text = "[Voice Message: audio transcription is not configured in this environment]"

    # 8. Claude Agent Loop
    reply_text = await agent.process_user_turn(
        wa_id=sender,
        user_text=user_text,
        image_bytes=image_bytes,
        image_mime=image_mime,
        is_confirmed_action=is_confirmed_action,
    )

    # 9. Send response back to user
    await whatsapp.send_text_message(
        to=sender,
        text=reply_text,
        reply_to_message_id=message_id,
    )


async def run_worker() -> None:
    """Standalone worker loop listening on Redis queue."""
    client = await default_store.get_client()
    logger.info("Worker started, listening for messages on Redis queue...")

    while True:
        try:
            # BRPOP blocks until an item arrives (timeout 5s)
            item = await client.brpop(REDIS_QUEUE_KEY, timeout=5)
            if item:
                _, raw_data = item
                message_payload = json.loads(raw_data)
                await process_message(message_payload)
        except asyncio.CancelledError:
            logger.info("Worker shutting down...")
            break
        except Exception as e:
            logger.error(f"Worker encountered unexpected error: {e}", exc_info=True)
            await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())
