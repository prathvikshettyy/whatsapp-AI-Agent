"""WhatsApp Webhook verification and ingestion endpoints."""

import json
from typing import Any, Dict, Optional
from fastapi import APIRouter, BackgroundTasks, Header, Query, Request, Response, status
from fastapi.responses import PlainTextResponse
import structlog

from backend.app.config import settings
from backend.app.security.signature import verify_meta_signature
from backend.app.services.ratelimit import get_redis
from backend.app.worker.tasks import process_inbound

logger = structlog.get_logger(__name__)
webhook_router = APIRouter()


@webhook_router.get("/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
) -> Response:
    """GET verification endpoint called by Meta when configuring webhook callback."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        if hub_challenge:
            logger.info("webhook_verification_successful")
            return PlainTextResponse(content=hub_challenge, status_code=status.HTTP_200_OK)

    logger.warning("webhook_verification_failed", mode=hub_mode)
    return Response(content="Forbidden", status_code=status.HTTP_403_FORBIDDEN)


@webhook_router.post("/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
) -> Response:
    """POST event delivery from Meta Cloud API."""
    raw_body = await request.body()

    # 1. Validate signature
    if not verify_meta_signature(settings.WHATSAPP_APP_SECRET, raw_body, x_hub_signature_256):
        logger.warning("webhook_invalid_signature")
        return Response(content="Invalid signature", status_code=status.HTTP_403_FORBIDDEN)

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        logger.error("webhook_json_parse_error", error=str(e))
        return Response(content="Bad request", status_code=status.HTTP_400_BAD_REQUEST)

    # 2. Extract messages (ignore statuses updates)
    redis_client = await get_redis()
    entries = payload.get("entry", [])

    for entry in entries:
        for change in entry.get("changes", []):
            val = change.get("value", {})
            if "statuses" in val and "messages" not in val:
                continue

            for msg in val.get("messages", []):
                msg_id = msg.get("id")
                if not msg_id:
                    continue

                # 3. Deduplicate on message.id (Redis SET NX EX 86400)
                is_new = await redis_client.set(f"wa:msg:{msg_id}", "1", nx=True, ex=86400)
                if not is_new:
                    logger.info("message_deduplicated_skipping", msg_id=msg_id)
                    continue

                # 4. Enqueue worker task
                background_tasks.add_task(process_inbound, {}, msg)

    # 5. Immediate 200 ACK to Meta
    return Response(
        content=json.dumps({"status": "ok"}),
        status_code=status.HTTP_200_OK,
        media_type="application/json",
    )
