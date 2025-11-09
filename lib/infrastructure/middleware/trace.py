"""
Trace ID middleware for request tracking.
"""

import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class TraceMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds trace ID to every request.

    Automatically includes trace_id, span_id in all logs.
    """

    def __init__(self, app: Callable, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract or generate trace context
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        parent_span_id = request.headers.get("X-Span-ID")
        caller_service = request.headers.get("X-Caller-Service")
        span_id = str(uuid.uuid4())

        # Bind trace context to structlog
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            caller_service=caller_service,
            service=self.service_name,
        )

        # Store in request state
        request.state.trace_id = trace_id
        request.state.span_id = span_id

        # Process request
        response = await call_next(request)

        # Add trace headers to response
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Span-ID"] = span_id
        response.headers["X-Service"] = self.service_name

        return response

