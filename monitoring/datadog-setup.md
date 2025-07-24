# Datadog APM Setup for Railway & Vercel

## Overview
This guide sets up comprehensive monitoring for TradeSense using Datadog APM, providing distributed tracing, metrics, and logs across all services.

## Prerequisites
- Datadog account (free trial available)
- Datadog API key
- Railway CLI installed
- Admin access to Railway projects

## Step 1: Install Datadog Agent

### For Each Railway Service

1. **Add Datadog tracing to requirements.txt**:
```txt
ddtrace>=1.18.0
datadog>=0.47.0
```

2. **Update service startup in each Dockerfile**:
```dockerfile
# Before
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# After (with Datadog APM)
CMD ["ddtrace-run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

3. **Add Datadog configuration to each service**:
```python
# src/config/datadog.py
import os
from ddtrace import config, tracer
from datadog import initialize, statsd

def setup_datadog():
    """Initialize Datadog APM and StatsD"""
    
    # APM Configuration
    tracer.configure(
        hostname=os.getenv('DD_AGENT_HOST', 'localhost'),
        port=int(os.getenv('DD_TRACE_AGENT_PORT', 8126)),
        enabled=os.getenv('DD_TRACE_ENABLED', 'true').lower() == 'true',
        analytics_enabled=True,
        env=os.getenv('DD_ENV', 'production'),
        service=os.getenv('DD_SERVICE', 'tradesense'),
        version=os.getenv('DD_VERSION', '1.0.0'),
    )
    
    # Service-specific tags
    tracer.set_tags({
        'service.name': os.getenv('SERVICE_NAME', 'unknown'),
        'railway.project': os.getenv('RAILWAY_PROJECT_ID', 'unknown'),
        'railway.environment': os.getenv('RAILWAY_ENVIRONMENT', 'production'),
    })
    
    # StatsD for custom metrics
    initialize(
        statsd_host=os.getenv('DD_AGENT_HOST', 'localhost'),
        statsd_port=int(os.getenv('DD_DOGSTATSD_PORT', 8125)),
    )
    
    return tracer, statsd

# Initialize at startup
tracer, metrics = setup_datadog()
```

## Step 2: Environment Variables

### Add to each Railway service:
```bash
# Datadog Configuration
DD_API_KEY=your-datadog-api-key
DD_SITE=datadoghq.com  # or datadoghq.eu
DD_ENV=production
DD_SERVICE=tradesense-gateway  # Change per service
DD_VERSION=1.0.0
DD_TRACE_ENABLED=true
DD_LOGS_INJECTION=true
DD_RUNTIME_METRICS_ENABLED=true
DD_PROFILING_ENABLED=true

# Service identification
SERVICE_NAME=gateway  # Change per service
```

## Step 3: Custom Instrumentation

### Add to main.py of each service:
```python
from fastapi import FastAPI, Request
from ddtrace import tracer
from datadog import statsd
import time

app = FastAPI()

# Middleware for custom tracing
@app.middleware("http")
async def add_tracing(request: Request, call_next):
    # Start span
    with tracer.trace("http.request") as span:
        span.set_tag("http.method", request.method)
        span.set_tag("http.url", str(request.url))
        
        # Track request timing
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Record metrics
        duration = (time.time() - start_time) * 1000  # ms
        statsd.histogram(
            "request.duration",
            duration,
            tags=[
                f"service:{os.getenv('SERVICE_NAME')}",
                f"endpoint:{request.url.path}",
                f"method:{request.method}",
                f"status:{response.status_code}"
            ]
        )
        
        # Add trace ID to response headers
        span.set_tag("http.status_code", response.status_code)
        response.headers["X-Trace-ID"] = str(span.trace_id)
        
        return response

# Custom business metrics
def track_order_created(order_id: str, amount: float):
    """Track order creation metrics"""
    statsd.increment("orders.created", tags=[f"service:trading"])
    statsd.histogram("orders.amount", amount, tags=[f"service:trading"])
    
    with tracer.trace("business.order.created") as span:
        span.set_tag("order.id", order_id)
        span.set_tag("order.amount", amount)

def track_ai_prediction(model: str, confidence: float, duration: float):
    """Track AI prediction metrics"""
    statsd.histogram(
        "ai.prediction.confidence",
        confidence,
        tags=[f"model:{model}"]
    )
    statsd.histogram(
        "ai.prediction.duration",
        duration,
        tags=[f"model:{model}"]
    )
```

## Step 4: Frontend Monitoring (Vercel)

### Install Datadog RUM:
```bash
cd frontend
npm install @datadog/browser-rum @datadog/browser-logs
```

### Add to app.html:
```html
<script>
  import { datadogRum } from '@datadog/browser-rum';
  import { datadogLogs } from '@datadog/browser-logs';
  
  // Initialize RUM
  datadogRum.init({
    applicationId: '%VITE_DD_APPLICATION_ID%',
    clientToken: '%VITE_DD_CLIENT_TOKEN%',
    site: 'datadoghq.com',
    service: 'tradesense-frontend',
    env: '%VITE_DD_ENV%',
    version: '%VITE_APP_VERSION%',
    sessionSampleRate: 100,
    sessionReplaySampleRate: 20,
    trackUserInteractions: true,
    trackResources: true,
    trackLongTasks: true,
    defaultPrivacyLevel: 'mask-user-input'
  });
  
  // Initialize Logs
  datadogLogs.init({
    clientToken: '%VITE_DD_CLIENT_TOKEN%',
    site: 'datadoghq.com',
    forwardErrorsToLogs: true,
    sessionSampleRate: 100,
  });
  
  // Start RUM
  datadogRum.startSessionReplayRecording();
</script>
```

## Step 5: Service Map Configuration

### Create service dependencies:
```python
# In Gateway service
@app.get("/api/v1/trades")
async def get_trades():
    with tracer.trace("gateway.get_trades"):
        # Trace call to Trading service
        with tracer.trace("http.call", service="trading-service"):
            response = await http_client.get(f"{TRADING_SERVICE_URL}/trades")
            
        # Trace call to Analytics service  
        with tracer.trace("http.call", service="analytics-service"):
            analytics = await http_client.get(f"{ANALYTICS_SERVICE_URL}/stats")
            
    return {"trades": response.json(), "analytics": analytics.json()}
```

## Step 6: Dashboards

### Create custom dashboards for:

1. **Service Health Dashboard**
   - Request rate by service
   - Error rate by service
   - P95 latency by endpoint
   - Active traces

2. **Business Metrics Dashboard**
   - Orders per minute
   - Trade volume
   - AI predictions per hour
   - User signups

3. **Infrastructure Dashboard**
   - Memory usage by service
   - CPU usage
   - Database connections
   - Redis operations

## Step 7: Alerts

### Configure alerts in Datadog:

```yaml
# High Error Rate
name: High Error Rate
query: "avg(last_5m):sum:trace.web.request.errors{env:production} by {service}.as_rate() > 0.05"
message: |
  Service {{service.name}} has error rate > 5%
  Current value: {{value}}
  [View Service Map](https://app.datadoghq.com/apm/services/{{service.name}})
tags:
  - team:backend
  - severity:high

# High Latency
name: High API Latency
query: "avg(last_5m):avg:trace.web.request.duration{env:production} by {service} > 1000"
message: |
  Service {{service.name}} has p95 latency > 1s
  Current value: {{value}}ms

# Database Issues
name: Database Connection Pool Exhausted
query: "avg(last_5m):avg:postgresql.connections.active{*} / avg:postgresql.connections.max{*} > 0.9"
message: |
  Database connection pool is >90% utilized
  Consider increasing pool size
```

## Step 8: Log Aggregation

### Configure structured logging:
```python
import logging
import json
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Log with trace context
def log_with_trace(level, message, **kwargs):
    span = tracer.current_span()
    if span:
        kwargs['dd.trace_id'] = span.trace_id
        kwargs['dd.span_id'] = span.span_id
    
    logger.log(level, message, extra=kwargs)

# Usage
log_with_trace(
    logging.INFO,
    "Order created",
    order_id=order_id,
    user_id=user_id,
    amount=amount
)
```

## Step 9: Cost Optimization

### Datadog cost management:
1. **Use sampling**: Set `DD_TRACE_SAMPLE_RATE=0.1` for 10% sampling
2. **Filter spans**: Only trace important operations
3. **Retention**: Set appropriate log retention (15 days default)
4. **Monitors**: Limit to critical alerts only

### Estimated costs:
- **APM**: ~$15/host/month (7 services = ~$105/month)
- **Logs**: ~$0.10/GB ingested
- **RUM**: ~$1.50/1000 sessions
- **Total estimate**: ~$150-200/month for full observability

## Step 10: Implementation Checklist

- [ ] Create Datadog account
- [ ] Install ddtrace in all services
- [ ] Configure environment variables in Railway
- [ ] Add custom instrumentation
- [ ] Set up frontend RUM
- [ ] Create dashboards
- [ ] Configure alerts
- [ ] Test distributed tracing
- [ ] Document runbooks
- [ ] Train team on Datadog

## Verification

### Test tracing is working:
```bash
# Generate test traffic
curl https://tradesense-gateway-production.up.railway.app/health

# Check Datadog APM
# Go to https://app.datadoghq.com/apm/services
# You should see all services appearing
```

### Verify metrics:
```bash
# Check custom metrics
# Go to https://app.datadoghq.com/metric/explorer
# Search for your custom metrics (orders.created, etc.)
```

## Troubleshooting

### No traces appearing:
1. Check DD_API_KEY is set correctly
2. Verify DD_TRACE_ENABLED=true
3. Check Railway logs for ddtrace errors
4. Ensure service has internet access

### Missing service dependencies:
1. Add explicit service tags in traces
2. Use consistent service names
3. Check trace propagation headers

### High costs:
1. Reduce trace sampling rate
2. Filter unnecessary logs
3. Disable profiling in development
4. Use tag-based retention

---

**Next Steps**: 
1. Sign up for Datadog trial
2. Run `railway-monitoring-setup.sh` to configure
3. Deploy services with new configuration
4. Access Datadog dashboard to view traces