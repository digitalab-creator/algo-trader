"""
Redis client - wrapper around redis-py.
"""

from __future__ import annotations

import json
import os
from typing import Any

import redis.asyncio as aioredis


class RedisClient:
    """
    Redis client with JSON serialization.

    Example:
        ```python
        await context.redis.set("key", {"data": "value"}, ttl=3600)
        data = await context.redis.get("key")
        ```
    """

    def __init__(self, redis_url: str | None = None):
        """
        Initialize Redis client.

        Args:
            redis_url: Redis URL (defaults to REDIS_URL env var)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client = aioredis.from_url(
            self.redis_url,
            decode_responses=True,
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "10")),
        )

    async def get(self, key: str) -> Any | None:
        """Get value from Redis (auto-deserializes JSON)."""
        value = await self.client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in Redis (auto-serializes to JSON)."""
        if not isinstance(value, str):
            value = json.dumps(value)

        if ttl:
            return await self.client.setex(key, ttl, value)
        else:
            return await self.client.set(key, value)

    async def delete(self, key: str) -> int:
        """Delete key from Redis."""
        return await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.client.exists(key) > 0

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        return await self.client.incrby(key, amount)

    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement counter."""
        return await self.client.decrby(key, amount)

    async def health_check(self) -> bool:
        """Check if Redis is reachable."""
        try:
            await self.client.ping()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        await self.client.close()

