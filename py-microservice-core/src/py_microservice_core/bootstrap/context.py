"""
Microservice context - holds all shared infrastructure clients.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from py_microservice_core.internal.api_clients.manager import APIClientManager
    from py_microservice_core.internal.database.client import DatabaseClient
    from py_microservice_core.internal.monitoring.client import MonitoringClient
    from py_microservice_core.internal.redis_client.client import RedisClient


class MicroserviceContext:
    """
    Context object passed to all routes.

    Provides access to:
    - db: Database client (PostgreSQL + SQLAlchemy)
    - redis: Redis client
    - api_clients: HTTP API clients with circuit breaker + cache
    - monitoring: Monitoring/metrics client

    Example:
        ```python
        @router.get("/users")
        async def get_users(context: MicroserviceContext = Depends(get_context)):
            async with context.db.session() as session:
                result = await session.execute(select(User))
                return result.scalars().all()
        ```
    """

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        self.db: Optional[DatabaseClient] = None
        self.redis: Optional[RedisClient] = None
        self.api_clients: Optional[APIClientManager] = None
        self.monitoring: Optional[MonitoringClient] = None

    def __repr__(self) -> str:
        features = []
        if self.db:
            features.append("db")
        if self.redis:
            features.append("redis")
        if self.api_clients:
            features.append("api_clients")
        if self.monitoring:
            features.append("monitoring")

        return f"<MicroserviceContext({self.service_name}) features={features}>"

