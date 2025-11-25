"""
Middleware components for The Good Shepherd API.
Provides request tracking, logging, and monitoring.
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

from backend.core.logging import get_logger

logger = get_logger(__name__)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking and logging HTTP requests.
    Adds request ID to all requests and logs request/response details.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Bind request context
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )

        # Log incoming request
        logger.info(
            "request_started",
            query_params=dict(request.query_params),
            headers={k: v for k, v in request.headers.items()
                    if k.lower() not in ['authorization', 'cookie']},
        )

        # Track request timing
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_seconds=round(duration, 4),
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # Calculate duration even on error
            duration = time.time() - start_time

            # Log error
            logger.error(
                "request_failed",
                error=str(exc),
                error_type=type(exc).__name__,
                duration_seconds=round(duration, 4),
                exc_info=True,
            )

            # Re-raise to let FastAPI's exception handler deal with it
            raise

        finally:
            # Clear context
            structlog.contextvars.clear_contextvars()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding security headers to responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Don't add HSTS in development
        # In production, this should be handled by reverse proxy

        return response
