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
    redis_client = await get_redis()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(REDIS_EVENTS_CHANNEL)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break

                # Non-blocking get_message with timeout to allow pinging
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    data = message.get("data")
                    yield f"data: {data}\n\n"

                # 15s Heartbeat ping per specification
                now = time.time()
                if int(now) % 15 == 0:
                    yield f": ping - {now}\n\n"

                await asyncio.sleep(0.5)
        finally:
            await pubsub.unsubscribe(REDIS_EVENTS_CHANNEL)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
