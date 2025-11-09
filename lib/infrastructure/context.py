"""
Application context - holds all shared infrastructure clients.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from lib.infrastructure.database.client import DatabaseClient
    from lib.infrastructure.monitoring.client import MonitoringClient
    from lib.infrastructure.redis_client.client import RedisClient


class AppContext:
    """
    Context object holding all infrastructure clients.

    Provides access to:
    - db: Database client (PostgreSQL + SQLAlchemy)
    - redis: Redis client
    - monitoring: Monitoring/metrics client

    Example:
        ```python
        async with context.db.session() as session:
            result = await session.execute(select(Trade))
            return result.scalars().all()
        ```
    """

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        self.db: Optional[DatabaseClient] = None
        self.redis: Optional[RedisClient] = None
        self.monitoring: Optional[MonitoringClient] = None

    def __repr__(self) -> str:
        features = []
        if self.db:
            features.append("db")
        if self.redis:
            features.append("redis")
        if self.monitoring:
            features.append("monitoring")

        return f"<AppContext({self.service_name}) features={features}>"

