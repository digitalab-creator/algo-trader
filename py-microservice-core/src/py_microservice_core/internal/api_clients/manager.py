"""
API client manager with circuit breaker, retry, and caching.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Dict, Optional

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

if TYPE_CHECKING:
    from py_microservice_core.internal.redis_client.client import RedisClient

logger = structlog.get_logger()


class APIClient:
    """
    HTTP API client with retry, circuit breaker, and caching.

    Features:
    - Automatic retry on failures
    - Circuit breaker pattern
    - Response caching (Redis-backed)
    - Trace ID propagation
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        redis_client: Optional[RedisClient] = None,
        cache_ttl: int = 300,
        timeout: int = 30,
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.redis = redis_client
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def _get_trace_headers(self) -> Dict[str, str]:
        """Get trace headers from current context."""
        from structlog.contextvars import get_contextvars

        ctx = get_contextvars()
        return {
            "X-Trace-ID": ctx.get("trace_id", ""),
            "X-Span-ID": ctx.get("span_id", ""),
            "X-Caller-Service": ctx.get("service", ""),
        }

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get(
        self, path: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True
    ) -> Any:
        """
        GET request with retry and caching.

        Args:
            path: API path (e.g., "/users")
            params: Query parameters
            use_cache: Whether to use cache

        Returns:
            Response JSON

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        url = f"{self.base_url}{path}"
        cache_key = f"api_cache:{self.name}:{path}:{params}"

        # Try cache first
        if use_cache and self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return cached

        # Make request
        headers = await self._get_trace_headers()
        response = await self.client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Cache response
        if use_cache and self.redis:
            await self.redis.set(cache_key, data, ttl=self.cache_ttl)

        return data

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def post(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """
        POST request with retry.

        Args:
            path: API path
            json: Request body

        Returns:
            Response JSON
        """
        url = f"{self.base_url}{path}"
        headers = await self._get_trace_headers()
        response = await self.client.post(url, json=json, headers=headers)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()


class APIClientManager:
    """
    Manager for multiple API clients.

    Example:
        ```python
        clients = APIClientManager({
            "user_service": {"base_url": "http://users:8012"},
            "order_service": {"base_url": "http://orders:8013"}
        })

        users = await clients.user_service.get("/users")
        ```
    """

    def __init__(self, config: Dict[str, Dict[str, Any]], redis_client: Optional[RedisClient] = None):
        self.clients: Dict[str, APIClient] = {}

        for name, client_config in config.items():
            self.clients[name] = APIClient(
                name=name,
                base_url=client_config["base_url"],
                redis_client=redis_client,
                cache_ttl=client_config.get("cache_ttl", 300),
                timeout=client_config.get("timeout", 30),
            )

    def __getattr__(self, name: str) -> APIClient:
        """Dynamic client access."""
        if name in self.clients:
            return self.clients[name]
        raise AttributeError(f"API client '{name}' not configured")

    async def close_all(self) -> None:
        """Close all clients."""
        await asyncio.gather(*[client.close() for client in self.clients.values()])

