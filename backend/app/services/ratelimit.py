"""Rate limiting service using Redis sliding window."""

import time
from typing import Optional
import redis.asyncio as aioredis

from backend.app.config import settings

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def check_rate_limit(wa_id: str, limit: int = 10, window: int = 60) -> bool:
    """Sliding window rate limit using Redis Sorted Set."""
    client = await get_redis()
    key = f"wa:ratelimit:{wa_id}"
    now = time.time()
    clear_before = now - window

    pipe = client.pipeline()
    pipe.zremrangebyscore(key, 0, clear_before)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window + 10)
    results = await pipe.execute()

    return results[2] <= limit
