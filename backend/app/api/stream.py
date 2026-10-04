"""Server-Sent Events (SSE) live streaming endpoint."""

import asyncio
import time
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import structlog

from backend.app.services.events import REDIS_EVENTS_CHANNEL
from backend.app.services.ratelimit import get_redis

logger = structlog.get_logger(__name__)
stream_router = APIRouter(tags=["stream"])


@stream_router.get("/stream")
async def event_stream(request: Request):
    """Subscribe to live WhatsApp chat events and handoff alerts via SSE."""
    has_redis = False
    pubsub = None

    try:
        redis_client = await get_redis()
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(REDIS_EVENTS_CHANNEL)
        has_redis = True
    except Exception as e:
        logger.warning("sse_redis_unavailable_fallback_to_heartbeat", error=str(e))

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break

                if has_redis and pubsub:
                    try:
                        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                        if message and message.get("type") == "message":
                            data = message.get("data")
                            yield f"data: {data}\n\n"
                    except Exception:
                        pass

                # 15s Heartbeat ping per specification
                now = time.time()
                if int(now) % 15 == 0:
                    yield f": ping - {now}\n\n"

                await asyncio.sleep(1.0)
        finally:
            if has_redis and pubsub:
                try:
                    await pubsub.unsubscribe(REDIS_EVENTS_CHANNEL)
                except Exception:
                    pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
