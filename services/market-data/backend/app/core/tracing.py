"""
OpenTelemetry instrumentation for distributed tracing
"""
import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.trace import Status, StatusCode
from opentelemetry.semconv.trace import SpanAttributes

from fastapi import FastAPI, Request
from sqlalchemy import Engine

logger = logging.getLogger(__name__)

# Global tracer instance
tracer: Optional[trace.Tracer] = None


def setup_tracing(
    app: FastAPI,
    service_name: str = "tradesense-backend",
    service_version: str = "1.0.0",
    environment: str = "production",
    otlp_endpoint: str = None,
    enabled: bool = True
) -> None:
    """
    Set up OpenTelemetry tracing for the application
    
    Args:
        app: FastAPI application instance
        service_name: Name of the service
        service_version: Version of the service
        environment: Environment (production, staging, development)
        otlp_endpoint: OTLP exporter endpoint
        enabled: Whether tracing is enabled
    """
    global tracer
    
    if not enabled:
        logger.info("Tracing is disabled")
        return
    
    # Set default endpoint if not provided
    if not otlp_endpoint:
        otlp_endpoint = os.getenv("OTLP_ENDPOINT", "tempo-distributor.monitoring:4317")
    
    try:
        # Create resource attributes
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "service.environment": environment,
            "service.namespace": "tradesense",
            "deployment.environment": environment,
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Create OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=True,  # Use TLS in production
            headers={}  # Add authentication headers if needed
        )
        
        # Add batch span processor
        span_processor = BatchSpanProcessor(
            otlp_exporter,
            max_queue_size=2048,
            max_export_batch_size=512,
            max_export_timeout_millis=30000,
        )
        provider.add_span_processor(span_processor)
        
        # Set the tracer provider
        trace.set_tracer_provider(provider)
        
        # Set propagator
        set_global_textmap(TraceContextTextMapPropagator())
        
        # Get tracer
        tracer = trace.get_tracer(
            instrumenting_module_name=__name__,
            instrumenting_library_version=service_version
        )
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health,metrics,docs,redoc,openapi.json",
            server_request_hook=server_request_hook,
            client_request_hook=client_request_hook,
            client_response_hook=client_response_hook,
        )
        
        # Instrument other libraries
        SQLAlchemyInstrumentor().instrument()
        RedisInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        LoggingInstrumentor().instrument(set_logging_format=True)
        
        logger.info(f"Tracing initialized with endpoint: {otlp_endpoint}")
        
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")
        raise


def server_request_hook(span: trace.Span, scope: Dict[str, Any]) -> None:
    """
    Hook to add custom attributes to server spans
    """
    if span and span.is_recording():
        # Add custom attributes
        span.set_attribute("http.user_agent", scope.get("headers", {}).get(b"user-agent", [b""])[0].decode())
        span.set_attribute("http.real_ip", scope.get("headers", {}).get(b"x-real-ip", [b""])[0].decode())
        
        # Add user context if available
        if hasattr(scope.get("app"), "state") and hasattr(scope["app"].state, "user"):
            user = scope["app"].state.user
            span.set_attribute("user.id", str(user.id))
            span.set_attribute("user.email", user.email)


def client_request_hook(span: trace.Span, request: Request) -> None:
    """
    Hook to add custom attributes to client request spans
    """
    if span and span.is_recording():
        span.set_attribute("http.request.body.size", len(request.content) if hasattr(request, "content") else 0)


def client_response_hook(span: trace.Span, request: Request, response) -> None:
    """
    Hook to add custom attributes to client response spans
    """
    if span and span.is_recording():
        span.set_attribute("http.response.body.size", len(response.content) if hasattr(response, "content") else 0)
        
        # Set span status based on response
        if hasattr(response, "status_code"):
            if response.status_code >= 400:
                span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))


@contextmanager
def trace_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL
):
    """
    Context manager for creating custom spans
    
    Usage:
        with trace_span("custom_operation", {"key": "value"}):
            # Your code here
            pass
    """
    if not tracer:
        yield None
        return
    
    with tracer.start_as_current_span(
        name,
        kind=kind,
        attributes=attributes or {}
    ) as span:
        try:
            yield span
        except Exception as e:
            if span and span.is_recording():
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """
    Add an event to the current span
    
    Args:
        name: Event name
        attributes: Event attributes
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.add_event(name, attributes or {})


def set_span_attributes(attributes: Dict[str, Any]) -> None:
    """
    Set attributes on the current span
    
    Args:
        attributes: Dictionary of attributes to set
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


def record_exception(exception: Exception) -> None:
    """
    Record an exception in the current span
    
    Args:
        exception: Exception to record
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))


# Decorator for tracing functions
def trace_function(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace function execution
    
    Usage:
        @trace_function("custom_name", {"key": "value"})
        def my_function():
            pass
    """
    def decorator(func):
        span_name = name or f"{func.__module__}.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            with trace_span(span_name, attributes):
                return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            with trace_span(span_name, attributes):
                return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# SQL query tracing helper
def trace_sql_query(query: str, params: Optional[Dict[str, Any]] = None) -> None:
    """
    Helper to trace SQL queries with proper attributes
    
    Args:
        query: SQL query string
        params: Query parameters
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_attribute(SpanAttributes.DB_STATEMENT, query)
        if params:
            span.set_attribute("db.params", str(params))


# Cache operation tracing
@contextmanager
def trace_cache_operation(
    operation: str,
    cache_key: str,
    cache_name: str = "redis"
):
    """
    Context manager for tracing cache operations
    
    Args:
        operation: Cache operation (get, set, delete, etc.)
        cache_key: Cache key
        cache_name: Name of the cache system
    """
    with trace_span(
        f"cache.{operation}",
        attributes={
            "cache.operation": operation,
            "cache.key": cache_key,
            "cache.system": cache_name
        },
        kind=trace.SpanKind.CLIENT
    ) as span:
        yield span


# External API call tracing
@contextmanager
def trace_external_call(
    service_name: str,
    operation: str,
    url: Optional[str] = None
):
    """
    Context manager for tracing external API calls
    
    Args:
        service_name: Name of the external service
        operation: Operation being performed
        url: URL being called
    """
    attributes = {
        "external.service": service_name,
        "external.operation": operation
    }
    if url:
        attributes["http.url"] = url
    
    with trace_span(
        f"{service_name}.{operation}",
        attributes=attributes,
        kind=trace.SpanKind.CLIENT
    ) as span:
        yield span


# Middleware for adding trace context to logs
class TraceContextLoggingMiddleware:
    """
    Middleware to add trace context to log records
    """
    def __init__(self, app: FastAPI):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        # Get current span
        span = trace.get_current_span()
        
        if span and span.is_recording():
            # Get trace context
            span_context = span.get_span_context()
            trace_id = format(span_context.trace_id, "032x")
            span_id = format(span_context.span_id, "016x")
            
            # Add to request state for access in logs
            request.state.trace_id = trace_id
            request.state.span_id = span_id
            
            # Add to logging context
            import logging
            logging_extra = {
                "trace_id": trace_id,
                "span_id": span_id
            }
            
            # Process request with logging context
            with logging.LoggerAdapter(logger, logging_extra):
                response = await call_next(request)
        else:
            response = await call_next(request)
        
        return response


import asyncio