"""
Algo-Fleet API - Algorithmic Trading Platform

Main application setup using centralized infrastructure.
"""

from lib.infrastructure import setup_app
from app.routes import trades_router

# Setup application with centralized infrastructure
app, context = setup_app(
    service_name="algo-fleet",
    port=8000,
    features={
        "database": True,
        "redis": True,
    },
    routers=[trades_router],
    log_level="INFO",
)

# Export for use in other modules
__all__ = ["app", "context"]

