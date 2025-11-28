"""OpenTelemetry instrumentation for Good Shepherd API."""

import logging
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

logger = logging.getLogger(__name__)

# Configuration from environment
OTEL_ENABLED = os.getenv("OTEL_ENABLED", "true").lower() == "true"
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "good-shepherd-api")
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")


def setup_telemetry(app) -> Optional[TracerProvider]:
    """
    Configure OpenTelemetry for the FastAPI application.
    
    Returns the TracerProvider if telemetry is enabled, None otherwise.
    """
    if not OTEL_ENABLED:
        logger.info("OpenTelemetry disabled via OTEL_ENABLED=false")
        return None
    
    # Create resource with service info
    resource = Resource.create({
        "service.name": OTEL_SERVICE_NAME,
        "service.version": "0.3.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Add exporters
    if OTEL_EXPORTER_OTLP_ENDPOINT:
        # Use OTLP exporter for production (Jaeger, Zipkin, etc.)
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            otlp_exporter = OTLPSpanExporter(endpoint=OTEL_EXPORTER_OTLP_ENDPOINT)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info(f"OpenTelemetry OTLP exporter configured: {OTEL_EXPORTER_OTLP_ENDPOINT}")
        except Exception as e:
            logger.warning(f"Failed to configure OTLP exporter: {e}")
    else:
        # Use console exporter for development
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("OpenTelemetry console exporter configured (development mode)")
    
    # Set global tracer provider
    trace.set_tracer_provider(provider)
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    logger.info("FastAPI instrumented with OpenTelemetry")
    
    # Instrument logging to include trace context
    LoggingInstrumentor().instrument(set_logging_format=True)
    logger.info("Logging instrumented with OpenTelemetry trace context")
    
    return provider


def get_tracer(name: str = __name__):
    """Get a tracer instance for manual instrumentation."""
    return trace.get_tracer(name)


# Middleware for request logging
class RequestLoggingMiddleware:
    """Middleware to log all incoming requests with timing."""
    
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("good_shepherd.requests")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        import time
        start_time = time.time()
        
        # Extract request info
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        client = scope.get("client", ("unknown", 0))
        client_ip = client[0] if client else "unknown"
        
        # Track response status
        response_status = [0]
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response_status[0] = message.get("status", 0)
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.info(
                f"{method} {path} - {response_status[0]} - {duration_ms:.2f}ms - {client_ip}"
            )
