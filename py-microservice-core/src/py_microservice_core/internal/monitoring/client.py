"""
Monitoring client - metrics and events backed by Redis.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from py_microservice_core.internal.redis_client.client import RedisClient


class MonitoringClient:
    """
    Monitoring client for metrics and events.

    Backed by Redis for persistence across restarts.

    Example:
        ```python
        context.monitoring.metric("api.requests", 1)
        context.monitoring.event("user.created", user_id=123)
        ```
    """

    def __init__(self, redis_client: RedisClient, service_name: str):
        """
        Initialize monitoring client.

        Args:
            redis_client: Redis client instance (REQUIRED!)
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
            value: Metric value (default: 1.0 for counters)
            tags: Optional tags for filtering

        Example:
            ```python
            await monitoring.metric("api.requests", 1)
            await monitoring.metric("response.time", 0.234, tags={"endpoint": "/users"})
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
            event_type: Event type (e.g., "user.created")
            **data: Event data

        Example:
            ```python
            await monitoring.event("user.created", user_id=123, email="user@example.com")
            ```
        """
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }

        key = f"{self.prefix}:events:{event_type}"
        await self.redis.client.lpush(key, event)
        await self.redis.client.ltrim(key, 0, 99)  # Keep last 100 events

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot.

        Returns:
            Dict of all metrics

        Note: This is a synchronous method for HTTP endpoints
        """
        # TODO: Implement async gathering of metrics
        return {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {},
        }

