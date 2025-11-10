"""
Example: Simple microservice with database and Redis.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select

from py_microservice_core import setup_microservice
from py_microservice_core.bootstrap.context import MicroserviceContext

# Create router
router = APIRouter(prefix="/api", tags=["example"])


# Dependency to get context
def get_context() -> MicroserviceContext:
    """Get microservice context (injected by setup)."""
    # This will be properly injected in production
    # For now, this is a placeholder
    raise NotImplementedError("Context injection not shown in example")


@router.get("/users")
async def list_users(context: MicroserviceContext = Depends(get_context)):
    """
    List all users from database.

    Example of using database context.
    """
    async with context.db.session() as session:
        # result = await session.execute(select(User))
        # users = result.scalars().all()
        # return users
        return {"users": []}


@router.get("/cache-test")
async def cache_test(context: MicroserviceContext = Depends(get_context)):
    """
    Test Redis cache.

    Example of using Redis context.
    """
    # Try to get from cache
    cached_value = await context.redis.get("test_key")

    if cached_value:
        return {"source": "cache", "value": cached_value}

    # Not in cache, compute and store
    new_value = {"computed": "data", "timestamp": "2025-11-09"}
    await context.redis.set("test_key", new_value, ttl=300)

    return {"source": "computed", "value": new_value}


@router.post("/metric")
async def record_metric(context: MicroserviceContext = Depends(get_context)):
    """
    Record a metric.

    Example of using monitoring context.
    """
    await context.monitoring.metric("api.custom_action", 1)
    await context.monitoring.event("custom_action.triggered", user_id=123)

    return {"status": "metric recorded"}


# Setup microservice
if __name__ == "__main__":
    import uvicorn

    app, context = setup_microservice(
        service_name="example-service",
        port=8000,
        features={
            "database": True,
            "redis": True,
            "api_clients": {
                "external_api": {
                    "base_url": "https://api.example.com",
                    "cache_ttl": 600,
                }
            },
        },
        routers=[router],
    )

    # Run with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

