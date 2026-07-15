"""Backend middleware for observability and rate limiting."""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware to log and monitor all API requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log metrics."""
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", str(time.time()))

        # Store request ID in state
        request.state.request_id = request_id
        request.state.start_time = start_time

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log request
            logger.info(
                f"Request: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Duration: {process_time:.3f}s "
                f"RequestID: {request_id}"
            )

            # Add timing headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id

            return response
        except Exception as exc:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"Error: {str(exc)} "
                f"Duration: {process_time:.3f}s "
                f"RequestID: {request_id}",
                exc_info=True,
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_times = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting."""
        client_ip = request.client.host
        current_time = time.time()

        if client_ip not in self.request_times:
            self.request_times[client_ip] = []

        # Clean old requests (older than 1 minute)
        self.request_times[client_ip] = [
            t for t in self.request_times[client_ip]
            if current_time - t < 60
        ]

        # Check limit
        if len(self.request_times[client_ip]) >= self.requests_per_minute:
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
            )

        # Record request
        self.request_times[client_ip].append(current_time)

        return await call_next(request)
