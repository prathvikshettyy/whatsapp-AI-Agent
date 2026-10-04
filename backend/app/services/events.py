"""Redis pub/sub event publisher for real-time dashboard SSE."""

import json
from typing import Any, Dict
from backend.app.services.ratelimit import get_redis

REDIS_EVENTS_CHANNEL = "wa:events_channel"


async def publish_event(event_type: str, data: Dict[str, Any]) -> None:
    client = await get_redis()
    payload = json.dumps({"event": event_type, "data": data})
    await client.publish(REDIS_EVENTS_CHANNEL, payload)
