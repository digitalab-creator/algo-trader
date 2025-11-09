"""
Monitoring client - metrics and events backed by Redis.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from lib.infrastructure.redis_client.client import RedisClient


class MonitoringClient:
    """
    Monitoring client for metrics and events.

    Backed by Redis for persistence.

    Example:
        ```python
        await context.monitoring.metric("api.requests", 1)
        await context.monitoring.event("trade.executed", symbol="AAPL", qty=100)
        ```
    """

    def __init__(self, redis_client: RedisClient, service_name: str):
        """
        Initialize monitoring client.

        Args:
            redis_client: Redis client instance
            service_name: Name of the service
        """
        if not redis_client:
            raise ValueError("Redis client is required for monitoring!")

        self.redis = redis_client
        self.service_name = service_name
        self.prefix = f"metrics:{service_name}"

    async def metric(self, name: str, value: float = 1.0, tags: Dict[str, Any] | None = None) -> None:
        """
        Record a metric.

        Args:
            name: Metric name (e.g., "api.requests")
            value: Metric value (default: 1.0)
            tags: Optional tags

        Example:
            ```python
            await monitoring.metric("trade.executed", 1)
            await monitoring.metric("response.time", 0.234, tags={"endpoint": "/trades"})
            ```
        """
        key = f"{self.prefix}:{name}"
        await self.redis.increment(key, int(value))

        # Store tags if provided
        if tags:
            tag_key = f"{key}:tags"
            await self.redis.set(tag_key, tags, ttl=86400)  # 24h TTL

    async def event(self, event_type: str, **data: Any) -> None:
        """
        Record an event.

        Args:
            event_type: Event type (e.g., "trade.executed")
            **data: Event data

        Example:
            ```python
            await monitoring.event("trade.executed", symbol="AAPL", qty=100, price=150.0)
            ```
        """
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }

        key = f"{self.prefix}:events:{event_type}"
        await self.redis.client.lpush(key, json.dumps(event))
        await self.redis.client.ltrim(key, 0, 99)  # Keep last 100 events

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot.

        Returns:
            Dict of metrics
        """
        return {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {},
        }

