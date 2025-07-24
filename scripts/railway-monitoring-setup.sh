#!/bin/bash

# Railway Monitoring Setup Script
# Automated setup for Datadog APM monitoring on Railway

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SERVICES=(
    "gateway"
    "auth"
    "trading"
    "analytics"
    "market-data"
    "billing"
    "ai"
)

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v railway >/dev/null 2>&1; then
        error "Railway CLI not installed"
        echo "Install with: npm install -g @railway/cli"
        exit 1
    fi
    
    # Check Railway login
    if ! railway whoami >/dev/null 2>&1; then
        error "Not logged in to Railway"
        echo "Run: railway login"
        exit 1
    fi
    
    # Check if Datadog API key is provided
    if [[ -z "${DD_API_KEY:-}" ]]; then
        warning "DD_API_KEY environment variable not set"
        echo "Please enter your Datadog API key:"
        read -s DD_API_KEY
        export DD_API_KEY
    fi
    
    success "Prerequisites check passed"
}

# Update requirements.txt for each service
update_requirements() {
    local service=$1
    local req_file="services/$service/requirements.txt"
    
    log "Updating requirements.txt for $service..."
    
    if [[ -f "$req_file" ]]; then
        # Check if ddtrace is already in requirements
        if ! grep -q "ddtrace" "$req_file"; then
            echo "" >> "$req_file"
            echo "# Datadog APM" >> "$req_file"
            echo "ddtrace>=1.18.0" >> "$req_file"
            echo "datadog>=0.47.0" >> "$req_file"
            echo "pythonjsonlogger>=2.0.0" >> "$req_file"
            success "Added Datadog dependencies to $service"
        else
            log "Datadog dependencies already present in $service"
        fi
    else
        warning "requirements.txt not found for $service"
    fi
}

# Create Datadog configuration file
create_datadog_config() {
    local service=$1
    local config_dir="services/$service/src/config"
    local config_file="$config_dir/datadog.py"
    
    log "Creating Datadog configuration for $service..."
    
    mkdir -p "$config_dir"
    
    cat > "$config_file" << 'EOF'
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
EOF

    success "Created Datadog configuration for $service"
}

# Update main.py to include monitoring
update_main_py() {
    local service=$1
    local main_file="services/$service/src/main.py"
    
    log "Updating main.py for $service..."
    
    if [[ -f "$main_file" ]]; then
        # Create a backup
        cp "$main_file" "$main_file.backup"
        
        # Check if monitoring is already added
        if ! grep -q "from config.datadog import tracer, metrics" "$main_file"; then
            # Add imports at the beginning after other imports
            sed -i '1a\
import time\
import os\
from config.datadog import tracer, metrics' "$main_file"
            
            # Add middleware after app initialization
            # This is a simplified version - you may need to adjust based on actual file structure
            cat >> "$main_file.monitoring" << 'EOF'

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
        metrics.histogram(
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
EOF
            warning "Added monitoring middleware to $main_file.monitoring - manual integration required"
        else
            log "Monitoring already present in $service"
        fi
    else
        warning "main.py not found for $service"
    fi
}

# Update Dockerfile for each service
update_dockerfile() {
    local service=$1
    local dockerfile="services/$service/Dockerfile"
    
    log "Updating Dockerfile for $service..."
    
    if [[ -f "$dockerfile" ]]; then
        # Check if ddtrace-run is already in CMD
        if ! grep -q "ddtrace-run" "$dockerfile"; then
            # Backup original
            cp "$dockerfile" "$dockerfile.backup"
            
            # Update CMD to use ddtrace-run
            sed -i 's/CMD \["uvicorn"/CMD ["ddtrace-run", "uvicorn"/g' "$dockerfile"
            sed -i 's/CMD \["gunicorn"/CMD ["ddtrace-run", "gunicorn"/g' "$dockerfile"
            sed -i 's/CMD \["python"/CMD ["ddtrace-run", "python"/g' "$dockerfile"
            
            success "Updated Dockerfile for $service"
        else
            log "ddtrace-run already configured in $service"
        fi
    else
        warning "Dockerfile not found for $service"
    fi
}

# Set Railway environment variables
set_railway_env() {
    local service=$1
    
    log "Setting Railway environment variables for $service..."
    
    # Core Datadog configuration
    railway variables set DD_API_KEY="$DD_API_KEY" --service "tradesense-$service" || warning "Failed to set DD_API_KEY for $service"
    railway variables set DD_SITE="datadoghq.com" --service "tradesense-$service"
    railway variables set DD_ENV="production" --service "tradesense-$service"
    railway variables set DD_SERVICE="tradesense-$service" --service "tradesense-$service"
    railway variables set DD_VERSION="1.0.0" --service "tradesense-$service"
    railway variables set DD_TRACE_ENABLED="true" --service "tradesense-$service"
    railway variables set DD_LOGS_INJECTION="true" --service "tradesense-$service"
    railway variables set DD_RUNTIME_METRICS_ENABLED="true" --service "tradesense-$service"
    railway variables set DD_PROFILING_ENABLED="true" --service "tradesense-$service"
    railway variables set SERVICE_NAME="$service" --service "tradesense-$service"
    
    # For cost optimization, use sampling in non-critical services
    if [[ "$service" == "billing" ]] || [[ "$service" == "analytics" ]]; then
        railway variables set DD_TRACE_SAMPLE_RATE="0.1" --service "tradesense-$service"
    fi
    
    success "Environment variables set for $service"
}

# Create monitoring dashboard script
create_dashboard_script() {
    log "Creating dashboard configuration script..."
    
    cat > "scripts/datadog-dashboards.sh" << 'EOF'
#!/bin/bash

# Datadog Dashboard Configuration Script
# Creates custom dashboards using Datadog API

DD_API_KEY=${DD_API_KEY:-""}
DD_APP_KEY=${DD_APP_KEY:-""}

if [[ -z "$DD_API_KEY" ]] || [[ -z "$DD_APP_KEY" ]]; then
    echo "Please set DD_API_KEY and DD_APP_KEY environment variables"
    exit 1
fi

# Create Service Health Dashboard
curl -X POST "https://api.datadoghq.com/api/v1/dashboard" \
  -H "DD-API-KEY: ${DD_API_KEY}" \
  -H "DD-APPLICATION-KEY: ${DD_APP_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "TradeSense Service Health",
    "description": "Overall health monitoring for TradeSense microservices",
    "widgets": [
      {
        "definition": {
          "type": "query_value",
          "requests": [
            {
              "q": "avg:trace.web.request{env:production}.rollup(avg, 300)",
              "aggregator": "avg"
            }
          ],
          "title": "Average Request Rate"
        }
      },
      {
        "definition": {
          "type": "timeseries",
          "requests": [
            {
              "q": "avg:trace.web.request.duration{env:production} by {service}",
              "display_type": "line"
            }
          ],
          "title": "Service Latency"
        }
      }
    ]
  }'

echo "Dashboard creation script ready. Run with DD_APP_KEY set."
EOF

    chmod +x scripts/datadog-dashboards.sh
    success "Created dashboard configuration script"
}

# Create alert configuration
create_alerts() {
    log "Creating alert configurations..."
    
    mkdir -p monitoring/alerts
    
    cat > "monitoring/alerts/high-error-rate.json" << 'EOF'
{
  "name": "High Error Rate - {{service.name}}",
  "type": "metric alert",
  "query": "avg(last_5m):sum:trace.web.request.errors{env:production} by {service}.as_rate() > 0.05",
  "message": "Service {{service.name}} has error rate > 5%\\n\\nCurrent value: {{value}}\\n\\n@slack-tradesense-alerts",
  "tags": ["team:backend", "severity:high"],
  "options": {
    "thresholds": {
      "critical": 0.05,
      "warning": 0.02
    },
    "notify_no_data": true,
    "no_data_timeframe": 10
  }
}
EOF

    cat > "monitoring/alerts/high-latency.json" << 'EOF'
{
  "name": "High API Latency - {{service.name}}",
  "type": "metric alert",
  "query": "avg(last_5m):avg:trace.web.request.duration{env:production} by {service} > 1000",
  "message": "Service {{service.name}} has p95 latency > 1s\\n\\nCurrent value: {{value}}ms\\n\\n@slack-tradesense-alerts",
  "tags": ["team:backend", "severity:medium"],
  "options": {
    "thresholds": {
      "critical": 1000,
      "warning": 500
    }
  }
}
EOF

    success "Created alert configurations"
}

# Create logging configuration
create_logging_config() {
    local service=$1
    local config_file="services/$service/src/config/logging.py"
    
    log "Creating logging configuration for $service..."
    
    cat > "$config_file" << 'EOF'
import logging
import json
from pythonjsonlogger import jsonlogger
from ddtrace import tracer

# Configure JSON logging
def setup_logging():
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter()
    logHandler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)
    return logger

# Log with trace context
def log_with_trace(logger, level, message, **kwargs):
    span = tracer.current_span()
    if span:
        kwargs['dd.trace_id'] = span.trace_id
        kwargs['dd.span_id'] = span.span_id
    
    logger.log(level, message, extra=kwargs)

logger = setup_logging()
EOF

    success "Created logging configuration for $service"
}

# Main setup process
main() {
    log "🚀 Starting Railway monitoring setup with Datadog..."
    
    check_prerequisites
    
    echo ""
    log "This script will:"
    echo "  1. Update requirements.txt files"
    echo "  2. Create Datadog configuration files"
    echo "  3. Update Dockerfiles to use ddtrace-run"
    echo "  4. Set Railway environment variables"
    echo "  5. Create monitoring dashboards and alerts"
    echo ""
    
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Setup cancelled"
        exit 0
    fi
    
    # Setup each service
    for service in "${SERVICES[@]}"; do
        echo ""
        log "Setting up monitoring for $service..."
        
        update_requirements "$service"
        create_datadog_config "$service"
        update_main_py "$service"
        update_dockerfile "$service"
        create_logging_config "$service"
        set_railway_env "$service"
        
        echo ""
    done
    
    # Create shared resources
    create_dashboard_script
    create_alerts
    
    echo ""
    success "✨ Monitoring setup complete!"
    
    echo ""
    echo "📋 Next steps:"
    echo "1. Review and integrate the .monitoring files into your main.py files"
    echo "2. Commit and push changes to trigger new deployments"
    echo "3. Log into Datadog to view incoming traces"
    echo "4. Run scripts/datadog-dashboards.sh to create dashboards"
    echo "5. Configure alerts in Datadog UI"
    echo ""
    echo "🔗 Useful links:"
    echo "- APM: https://app.datadoghq.com/apm/services"
    echo "- Metrics: https://app.datadoghq.com/metric/explorer"
    echo "- Logs: https://app.datadoghq.com/logs"
    
    warning "Remember to redeploy all services for changes to take effect!"
}

# Run main function
main "$@"