"""
py-microservice-core: Python microservice infrastructure package.

Provides FastAPI, PostgreSQL, Redis, monitoring, and more in a single setup function.
"""

from py_microservice_core.bootstrap.setup import setup_microservice
from py_microservice_core.internal.logger import get_logger
from py_microservice_core.middleware.trace import TraceMiddleware

__version__ = "1.0.0"
__all__ = ["setup_microservice", "get_logger", "TraceMiddleware"]

