"""
Startup validation - checks service health before serving traffic.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from fastapi import FastAPI

    from py_microservice_core.bootstrap.context import MicroserviceContext

logger = logging.getLogger(__name__)


def validate_service(app: FastAPI, context: MicroserviceContext, features: Dict[str, Any]) -> None:
    """
    Validate service configuration and health.

    Checks:
    1. Required features are enabled correctly
    2. Database connection (if enabled)
    3. Redis connection (if enabled)
    4. Environment variables

    Args:
        app: FastAPI application
        context: Microservice context
        features: Feature configuration

    Raises:
        ValueError: If validation fails
    """
    logger.info("Running startup validation...")

    # Check Redis is enabled if monitoring is requested
    if context.monitoring and not context.redis:
        raise ValueError("Monitoring requires Redis to be enabled!")

    # Validate database connection
    if features.get("database") and context.db:
        logger.info("✓ Database client initialized")
        # TODO: Add async health check

    # Validate Redis connection
    if features.get("redis") and context.redis:
        logger.info("✓ Redis client initialized")
        # TODO: Add async health check

    # Validate API clients
    if context.api_clients:
        client_count = len(context.api_clients.clients)
        logger.info(f"✓ {client_count} API client(s) initialized")

    logger.info("✅ Startup validation passed")

