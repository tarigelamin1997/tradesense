"""
Datadog APM Integration for Production Monitoring

Provides distributed tracing, metrics, and profiling
"""

import os
from typing import Dict, Any, Optional, Callable
from functools import wraps
import time
from contextlib import contextmanager
from ddtrace import tracer, patch_all, config
from ddtrace.profiling import Profiler
from datadog import initialize, statsd, DogStatsd
import logging

from core.config_env import get_env_config
from core.logging_config import get_logger

logger = get_logger(__name__)


class DatadogConfig:
    """Datadog configuration"""
    
    def __init__(self):
        self.api_key = os.getenv("DD_API_KEY", "")
        self.app_key = os.getenv("DD_APP_KEY", "")
        self.site = os.getenv("DD_SITE", "datadoghq.com")
        self.env = os.getenv("DD_ENV", "production")
        self.service = os.getenv("DD_SERVICE", "tradesense")
        self.version = os.getenv("DD_VERSION", "1.0.0")
        
        # APM settings
        self.trace_enabled = os.getenv("DD_TRACE_ENABLED", "true").lower() == "true"
        self.trace_sample_rate = float(os.getenv("DD_TRACE_SAMPLE_RATE", "0.1"))
        self.trace_agent_hostname = os.getenv("DD_AGENT_HOST", "localhost")
        self.trace_agent_port = int(os.getenv("DD_TRACE_AGENT_PORT", "8126"))
        
        # Profiling
        self.profiling_enabled = os.getenv("DD_PROFILING_ENABLED", "true").lower() == "true"
        
        # Metrics
        self.runtime_metrics_enabled = os.getenv("DD_RUNTIME_METRICS_ENABLED", "true").lower() == "true"
        self.logs_injection = os.getenv("DD_LOGS_INJECTION", "true").lower() == "true"
        
        # Service mapping
        self.service_mapping = {
            "gateway": "tradesense-gateway",
            "auth": "tradesense-auth",
            "trading": "tradesense-trading",
            "analytics": "tradesense-analytics",
            "billing": "tradesense-billing",
            "market-data": "tradesense-market-data",
            "ai": "tradesense-ai"
        }


class DatadogAPM:
    """Datadog APM integration"""
    
    def __init__(self, config: DatadogConfig):
        self.config = config
        self.tracer = tracer
        self.metrics = None
        self.profiler = None
        self._initialized = False
    
    def initialize(self, service_name: Optional[str] = None):
        """Initialize Datadog APM"""
        if self._initialized:
            return
        
        # Set service name
        if service_name:
            self.config.service = self.config.service_mapping.get(
                service_name, 
                f"tradesense-{service_name}"
            )
        
        # Configure tracer
        self.tracer.configure(
            hostname=self.config.trace_agent_hostname,
            port=self.config.trace_agent_port,
            enabled=self.config.trace_enabled,
            analytics_enabled=True,
            env=self.config.env,
            service=self.config.service,
            version=self.config.version,
            logs_injection=self.config.logs_injection,
            runtime_metrics_enabled=self.config.runtime_metrics_enabled,
            settings={
                "FILTERS": [
                    {
                        "name": "filter_health_check",
                        "pattern": "http.url:*/health",
                        "sample_rate": 0.001  # Only trace 0.1% of health checks
                    }
                ]
            }
        )
        
        # Set global tags
        self.tracer.set_tags({
            "env": self.config.env,
            "service": self.config.service,
            "version": self.config.version,
            "region": os.getenv("AWS_REGION", "us-east-1"),
            "deployment": os.getenv("RAILWAY_ENVIRONMENT", "unknown")
        })
        
        # Auto-patch libraries
        patch_all(
            logging=True,
            sqlalchemy=True,
            psycopg=True,
            redis=True,
            requests=True,
            asyncio=True,
            fastapi=True
        )
        
        # Initialize StatsD client
        self.metrics = DogStatsd(
            host=self.config.trace_agent_hostname,
            port=8125,
            namespace="tradesense",
            constant_tags=[
                f"env:{self.config.env}",
                f"service:{self.config.service}",
                f"version:{self.config.version}"
            ]
        )
        
        # Initialize profiler
        if self.config.profiling_enabled:
            self.profiler = Profiler(
                env=self.config.env,
                service=self.config.service,
                version=self.config.version,
                tags={
                    "region": os.getenv("AWS_REGION", "us-east-1")
                }
            )
            self.profiler.start()
            logger.info("Datadog profiler started")
        
        self._initialized = True
        logger.info(f"Datadog APM initialized for service: {self.config.service}")
    
    def trace_method(
        self, 
        operation_name: str, 
        service: Optional[str] = None,
        resource: Optional[str] = None,
        span_type: Optional[str] = None
    ):
        """Decorator to trace methods"""
        def decorator(func):
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.tracer.trace(
                    operation_name,
                    service=service or self.config.service,
                    resource=resource or func.__name__,
                    span_type=span_type
                ) as span:
                    # Add function metadata
                    span.set_tags({
                        "function.name": func.__name__,
                        "function.module": func.__module__
                    })
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_tag("result", "success")
                        return result
                    except Exception as e:
                        span.set_tag("error", True)
                        span.set_tag("error.type", type(e).__name__)
                        span.set_tag("error.msg", str(e))
                        raise
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.tracer.trace(
                    operation_name,
                    service=service or self.config.service,
                    resource=resource or func.__name__,
                    span_type=span_type
                ) as span:
                    span.set_tags({
                        "function.name": func.__name__,
                        "function.module": func.__module__
                    })
                    
                    try:
                        result = await func(*args, **kwargs)
                        span.set_tag("result", "success")
                        return result
                    except Exception as e:
                        span.set_tag("error", True)
                        span.set_tag("error.type", type(e).__name__)
                        span.set_tag("error.msg", str(e))
                        raise
            
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    @contextmanager
    def trace_operation(
        self,
        operation: str,
        tags: Optional[Dict[str, Any]] = None,
        measure: bool = True
    ):
        """Context manager for tracing operations"""
        start_time = time.time()
        
        with self.tracer.trace(operation) as span:
            if tags:
                span.set_tags(tags)
            
            try:
                yield span
                
                if measure and self.metrics:
                    duration = (time.time() - start_time) * 1000
                    self.metrics.histogram(
                        f"{operation}.duration",
                        duration,
                        tags=[f"operation:{operation}"]
                    )
                    self.metrics.increment(
                        f"{operation}.success",
                        tags=[f"operation:{operation}"]
                    )
                
            except Exception as e:
                span.set_tag("error", True)
                span.set_tag("error.type", type(e).__name__)
                span.set_tag("error.msg", str(e))
                
                if self.metrics:
                    self.metrics.increment(
                        f"{operation}.error",
                        tags=[
                            f"operation:{operation}",
                            f"error_type:{type(e).__name__}"
                        ]
                    )
                raise
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        metric_type: str = "gauge",
        tags: Optional[Dict[str, str]] = None
    ):
        """Record custom metric"""
        if not self.metrics:
            return
        
        tag_list = [f"{k}:{v}" for k, v in (tags or {}).items()]
        
        if metric_type == "gauge":
            self.metrics.gauge(metric_name, value, tags=tag_list)
        elif metric_type == "counter":
            self.metrics.increment(metric_name, value, tags=tag_list)
        elif metric_type == "histogram":
            self.metrics.histogram(metric_name, value, tags=tag_list)
        elif metric_type == "distribution":
            self.metrics.distribution(metric_name, value, tags=tag_list)
    
    def trace_request(self, request_type: str = "http"):
        """Middleware for tracing requests"""
        def middleware(request, call_next):
            # Extract trace context from headers
            trace_headers = {}
            for header in ["x-datadog-trace-id", "x-datadog-parent-id"]:
                if header in request.headers:
                    trace_headers[header] = request.headers[header]
            
            # Start span
            with self.tracer.trace(
                f"{request_type}.request",
                service=self.config.service,
                resource=f"{request.method} {request.url.path}",
                span_type="web"
            ) as span:
                # Set standard tags
                span.set_tags({
                    "http.method": request.method,
                    "http.url": str(request.url),
                    "http.path": request.url.path,
                    "http.host": request.url.hostname,
                    "user_agent": request.headers.get("user-agent", "unknown")
                })
                
                # Inject user context if available
                if hasattr(request.state, "user_id"):
                    span.set_tag("user.id", request.state.user_id)
                
                # Measure request
                start_time = time.time()
                
                try:
                    response = call_next(request)
                    
                    # Set response tags
                    span.set_tag("http.status_code", response.status_code)
                    
                    # Record metrics
                    duration = (time.time() - start_time) * 1000
                    self.record_metric(
                        "http.request.duration",
                        duration,
                        "histogram",
                        {
                            "method": request.method,
                            "endpoint": request.url.path,
                            "status": str(response.status_code)
                        }
                    )
                    
                    return response
                
                except Exception as e:
                    span.set_tag("error", True)
                    raise
        
        return middleware


# Business metrics tracking
class BusinessMetrics:
    """Track business-specific metrics"""
    
    def __init__(self, apm: DatadogAPM):
        self.apm = apm
    
    def track_user_signup(self, user_id: str, referral_source: Optional[str] = None):
        """Track new user signup"""
        self.apm.record_metric("users.signup", 1, "counter", {
            "referral_source": referral_source or "direct"
        })
        
        with self.apm.trace_operation("business.user.signup", {
            "user.id": user_id,
            "referral.source": referral_source
        }):
            logger.info(f"New user signup: {user_id}")
    
    def track_trade_execution(
        self,
        trade_id: str,
        symbol: str,
        trade_type: str,
        amount: float,
        duration_ms: float
    ):
        """Track trade execution"""
        self.apm.record_metric("trades.executed", 1, "counter", {
            "symbol": symbol,
            "type": trade_type
        })
        
        self.apm.record_metric("trades.amount", amount, "histogram", {
            "symbol": symbol,
            "type": trade_type
        })
        
        self.apm.record_metric("trades.execution_time", duration_ms, "histogram", {
            "symbol": symbol,
            "type": trade_type
        })
    
    def track_ai_prediction(
        self,
        model: str,
        prediction_type: str,
        confidence: float,
        duration_ms: float
    ):
        """Track AI prediction"""
        self.apm.record_metric("ai.predictions", 1, "counter", {
            "model": model,
            "type": prediction_type
        })
        
        self.apm.record_metric("ai.confidence", confidence, "gauge", {
            "model": model,
            "type": prediction_type
        })
        
        self.apm.record_metric("ai.inference_time", duration_ms, "histogram", {
            "model": model,
            "type": prediction_type
        })
    
    def track_revenue(
        self,
        amount: float,
        currency: str,
        source: str,
        user_id: str
    ):
        """Track revenue event"""
        self.apm.record_metric("revenue.amount", amount, "gauge", {
            "currency": currency,
            "source": source
        })
        
        with self.apm.trace_operation("business.revenue", {
            "amount": amount,
            "currency": currency,
            "source": source,
            "user.id": user_id
        }):
            logger.info(f"Revenue tracked: {amount} {currency} from {source}")


# Global APM instance
_apm: Optional[DatadogAPM] = None
_business_metrics: Optional[BusinessMetrics] = None


def get_apm() -> DatadogAPM:
    """Get global APM instance"""
    global _apm
    
    if _apm is None:
        config = DatadogConfig()
        _apm = DatadogAPM(config)
        
        # Initialize based on service
        service_name = os.getenv("SERVICE_NAME", "gateway")
        _apm.initialize(service_name)
    
    return _apm


def get_business_metrics() -> BusinessMetrics:
    """Get business metrics tracker"""
    global _business_metrics
    
    if _business_metrics is None:
        _business_metrics = BusinessMetrics(get_apm())
    
    return _business_metrics


# FastAPI integration
def setup_datadog_middleware(app):
    """Setup Datadog middleware for FastAPI"""
    from fastapi import Request
    
    apm = get_apm()
    
    @app.middleware("http")
    async def datadog_middleware(request: Request, call_next):
        """Trace all HTTP requests"""
        with apm.trace_operation(
            "http.request",
            tags={
                "http.method": request.method,
                "http.path": request.url.path
            }
        ) as span:
            # Extract user context
            if hasattr(request.state, "user_id"):
                span.set_tag("user.id", request.state.user_id)
            
            response = await call_next(request)
            
            # Set response tags
            span.set_tag("http.status_code", response.status_code)
            
            return response
    
    logger.info("Datadog middleware configured")