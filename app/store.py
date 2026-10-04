"""Redis-backed storage for chat history, deduplication, rate limiting, and state."""

import json
import time
from typing import Any, Dict, List, Optional
import redis.asyncio as aioredis

from app.config import settings


class RedisStore:
    """Manages Redis interactions for session state, dedupe, rate limits, and history."""

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self._redis = redis_client

    async def get_client(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                encoding="utf-8"
            )
        return self._redis

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    # --- Deduplication ---
    async def check_and_set_dedupe(self, message_id: str, ttl: int = 86400) -> bool:
        """
        Check if message_id has already been processed.
        Uses SET key 1 NX EX ttl.
        Returns True if message is new (processed first time), False if duplicate.
        """
        client = await self.get_client()
        key = f"wa:dedupe:{message_id}"
        # set with nx=True returns True if set, None/False if existed
        is_new = await client.set(key, "1", nx=True, ex=ttl)
        return bool(is_new)

    # --- Rate Limiting ---
    async def check_rate_limit(self, wa_id: str, limit: int = 10, window: int = 60) -> bool:
        """
        Sliding window rate limit using Redis Sorted Set.
        Returns True if within rate limit, False if limit exceeded.
        """
        client = await self.get_client()
        key = f"wa:ratelimit:{wa_id}"
        now = time.time()
        clear_before = now - window

        # Pipeline: remove older timestamps, add current timestamp, count remaining, set TTL
        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, clear_before)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window + 10)
        results = await pipe.execute()

        request_count = results[2]
        return request_count <= limit

    # --- Conversation History ---
    async def get_history(self, wa_id: str, max_turns: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieve the recent chat history for Claude.
        Returns messages in chronological order.
        """
        client = await self.get_client()
        key = f"wa:history:{wa_id}"
        # We store up to max_turns * 2 elements (each turn has user + assistant)
        raw_items = await client.lrange(key, -(max_turns * 2), -1)
        history: List[Dict[str, Any]] = []
        for item in raw_items:
            try:
                history.append(json.loads(item))
            except json.JSONDecodeError:
                continue
        return history

    async def add_turn(self, wa_id: str, role: str, content: Any, ttl: int = 604800) -> None:
        """
        Append a conversation turn to Redis.
        ttl defaults to 7 days.
        """
        client = await self.get_client()
        key = f"wa:history:{wa_id}"
        entry = json.dumps({"role": role, "content": content})
        pipe = client.pipeline()
        pipe.rpush(key, entry)
        # Keep maximum 50 messages stored per user to avoid unbounded list growth
        pipe.ltrim(key, -50, -1)
        pipe.expire(key, ttl)
        await pipe.execute()

    async def clear_history(self, wa_id: str) -> None:
        """Clear chat history for a given user."""
        client = await self.get_client()
        key = f"wa:history:{wa_id}"
        await client.delete(key)

    # --- Opt-Out / Honor Stop Policy ---
    async def is_opted_out(self, wa_id: str) -> bool:
        """Check whether the user has opted out of WhatsApp messages."""
        client = await self.get_client()
        key = f"wa:optout:{wa_id}"
        val = await client.get(key)
        return val == "1"

    async def set_opt_out(self, wa_id: str, opted_out: bool) -> None:
        """Set opt-out state for user (stops future bot replies)."""
        client = await self.get_client()
        key = f"wa:optout:{wa_id}"
        if opted_out:
            # Opt-out persisted indefinitely or until user texts 'start'
            await client.set(key, "1")
        else:
            await client.delete(key)

    # --- Human Handoff ---
    async def is_handed_off(self, wa_id: str) -> bool:
        """Check whether user conversation is routed to human agent."""
        client = await self.get_client()
        key = f"wa:handoff:{wa_id}"
        val = await client.get(key)
        return val == "1"

    async def set_handoff(self, wa_id: str, handed_off: bool, ttl: int = 86400) -> None:
        """Flag conversation for human agent support."""
        client = await self.get_client()
        key = f"wa:handoff:{wa_id}"
        if handed_off:
            await client.set(key, "1", ex=ttl)
        else:
            await client.delete(key)

    # --- Sensitive Action Confirmation ---
    async def set_pending_action(self, wa_id: str, action: Dict[str, Any], ttl: int = 600) -> None:
        """Store pending action requiring user confirmation (e.g. payments, order cancellation)."""
        client = await self.get_client()
        key = f"wa:pending_confirmation:{wa_id}"
        await client.set(key, json.dumps(action), ex=ttl)

    async def get_pending_action(self, wa_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve any pending sensitive action awaiting user confirmation."""
        client = await self.get_client()
        key = f"wa:pending_confirmation:{wa_id}"
        val = await client.get(key)
        if val:
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return None
        return None

    async def clear_pending_action(self, wa_id: str) -> None:
        """Clear pending action after execution or cancellation."""
        client = await self.get_client()
        key = f"wa:pending_confirmation:{wa_id}"
        await client.delete(key)


store = RedisStore()
