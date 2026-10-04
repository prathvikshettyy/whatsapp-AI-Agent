"""FastAPI application providing WhatsApp webhook verification and event routing."""

import hashlib
import hmac
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, FastAPI, Header, Query, Request, Response, status
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.store import store
from app.whatsapp import mask_phone_number, whatsapp_client
from app.worker import enqueue_message, process_message
from app.admin import admin_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def verify_meta_signature(app_secret: str, raw_body: bytes, signature_header: Optional[str]) -> bool:
    """
    Validate the X-Hub-Signature-256 header sent by Meta Cloud API.
    Header format: sha256=<hex_digest>
    """
    if not app_secret:
        # If no secret configured in test/dev environment, allow pass-through
        return True

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    received_sig = signature_header.split("sha256=", 1)[1]
    expected_sig = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_sig, received_sig)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("WhatsApp AI Agent application starting up...")
    yield
    logger.info("WhatsApp AI Agent application shutting down...")
    await store.close()
    await whatsapp_client.close()


app = FastAPI(
    title="WhatsApp AI Agent",
    description="Production WhatsApp Business Cloud API AI Agent powered by Claude",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(admin_router)



@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, str]:
    """Health check endpoint for container orchestrators."""
    return {"status": "healthy", "service": "whatsapp-ai-agent"}


@app.get("/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
) -> Response:
    """
    WhatsApp Webhook Verification Endpoint.
    Meta sends GET request with challenge token when setting up the callback URL.
    """
    logger.info(f"Webhook verification request received. Mode: {hub_mode}")

    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        if hub_challenge:
            logger.info("Webhook verification challenge successful.")
            return PlainTextResponse(content=hub_challenge, status_code=status.HTTP_200_OK)

    logger.warning("Webhook verification challenge failed. Mismatched verify token or mode.")
    return Response(
        content="Forbidden: Verification token mismatch",
        status_code=status.HTTP_403_FORBIDDEN,
    )


@app.post("/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
) -> Response:
    """
    WhatsApp Webhook Event Receiver.
    1. Validates HMAC-SHA256 signature against WHATSAPP_APP_SECRET.
    2. Parses incoming messages (ignoring statuses events).
    3. Dedupes using Redis SET NX EX 86400 on message ID.
    4. Enqueues background worker task.
    5. Immediately returns HTTP 200 OK.
    """
    raw_body = await request.body()

    # 1. Verify signature
    if not verify_meta_signature(settings.WHATSAPP_APP_SECRET, raw_body, x_hub_signature_256):
        logger.warning("Unauthorized webhook payload: invalid X-Hub-Signature-256 signature")
        return Response(content="Invalid signature", status_code=status.HTTP_403_FORBIDDEN)

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        logger.error(f"Failed to parse webhook JSON body: {e}")
        return Response(content="Bad Request", status_code=status.HTTP_400_BAD_REQUEST)

    # 2. Parse entries and messages
    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})

            # Ignore delivery/read 'statuses' events
            if "statuses" in value and "messages" not in value:
                continue

            messages = value.get("messages", [])
            for msg in messages:
                message_id = msg.get("id")
                sender = msg.get("from", "")

                if not message_id:
                    continue

                # 3. Deduplicate on message.id (Redis SET NX EX 86400)
                is_new = await store.check_and_set_dedupe(message_id, ttl=86400)
                if not is_new:
                    logger.info(
                        f"Deduplicated message {message_id} from {mask_phone_number(sender)}; skipping."
                    )
                    continue

                # 4. Enqueue processing task
                # Run via FastAPI BackgroundTasks for immediate handling
                background_tasks.add_task(process_message, msg)
                # Also push to Redis queue for standalone worker architectures
                background_tasks.add_task(enqueue_message, msg)

    # 5. Fast ACK to Meta
    return Response(
        content=json.dumps({"status": "ok"}),
        status_code=status.HTTP_200_OK,
        media_type="application/json",
    )
