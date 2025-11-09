"""
Main setup function for the application.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lib.infrastructure.context import AppContext
from lib.infrastructure.database.client import DatabaseClient
from lib.infrastructure.logger import setup_logging
from lib.infrastructure.middleware.trace import TraceMiddleware
from lib.infrastructure.monitoring.client import MonitoringClient
from lib.infrastructure.redis_client.client import RedisClient


def setup_app(
    service_name: str,
    port: int = 8000,
    features: Optional[Dict[str, Any]] = None,
    routers: Optional[List[Any]] = None,
    enable_cors: bool = True,
    log_level: str = "INFO",
) -> tuple[FastAPI, AppContext]:
    """
    Setup application with centralized infrastructure.

    Args:
        service_name: Name of the service
        port: Port to run on (default: 8000)
        features: Dict of feature flags:
            - database (bool): Enable PostgreSQL
            - redis (bool): Enable Redis
        routers: List of FastAPI routers to include
        enable_cors: Enable CORS middleware
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Tuple of (FastAPI app, AppContext)

    Example:
        ```python
        app, context = setup_app(
            service_name="algo-fleet",
            port=8000,
            features={"database": True, "redis": True}
        )
        ```
    """
    features = features or {}
    routers = routers or []

    # Setup logging
    setup_logging(service_name=service_name, level=log_level)
    logger = logging.getLogger(service_name)
    logger.info(f"Initializing {service_name} on port {port}")

    # Create FastAPI app
    app = FastAPI(
        title=service_name,
        version="1.0.0",
        description=f"{service_name} application",
    )

    # Add trace middleware (FIRST!)
    app.add_middleware(TraceMiddleware, service_name=service_name)

    # Add CORS if enabled
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Initialize context
    context = AppContext(service_name=service_name)

    # Setup database if requested
    if features.get("database"):
        logger.info("Initializing database connection")
        context.db = DatabaseClient()

    # Setup Redis if requested
    if features.get("redis"):
        logger.info("Initializing Redis connection")
        context.redis = RedisClient()

    # Setup monitoring (requires Redis!)
    if features.get("redis"):
        logger.info("Initializing monitoring")
        context.monitoring = MonitoringClient(redis_client=context.redis, service_name=service_name)
    else:
        logger.warning("Monitoring disabled - Redis is required!")

    # Register routers
    for router in routers:
        app.include_router(router)
        logger.info(f"Registered router: {router}")

    # Add health check endpoint
    @app.get("/health", tags=["system"])
    async def health() -> Dict[str, str]:
        """Health check endpoint."""
        return {
            "status": "ok",
            "service": service_name,
        }

    @app.get("/metrics", tags=["system"])
    async def metrics() -> Dict[str, Any]:
        """Metrics endpoint."""
        if context.monitoring:
            return context.monitoring.get_metrics()
        return {"error": "Monitoring not enabled"}

    logger.info(f"✅ {service_name} initialized successfully")

    return app, context

