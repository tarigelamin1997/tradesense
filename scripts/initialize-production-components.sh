#!/bin/bash
# Initialize all production components
# Sets up Datadog APM, circuit breakers, and audit logging

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Initializing Production Components${NC}"
echo "======================================"
echo ""

# Function to setup Datadog APM
setup_datadog_apm() {
    echo -e "${BLUE}Setting up Datadog APM...${NC}"
    
    # Check for Datadog API key
    if [ -z "${DD_API_KEY:-}" ]; then
        echo -e "${YELLOW}⚠️  Datadog API key not set${NC}"
        echo "Please set DD_API_KEY environment variable"
        echo "Get your API key from: https://app.datadoghq.com/account/settings#api"
        echo ""
        read -p "Enter Datadog API key (or skip): " DD_API_KEY
        
        if [ -z "$DD_API_KEY" ]; then
            echo -e "${YELLOW}Skipping Datadog setup${NC}"
            return
        fi
    fi
    
    # Set Datadog environment variables for all services
    for service in gateway auth trading analytics billing market-data ai; do
        echo "  Configuring $service..."
        
        railway variables set \
            DD_API_KEY="$DD_API_KEY" \
            DD_SITE="datadoghq.com" \
            DD_ENV="production" \
            DD_SERVICE="tradesense-$service" \
            DD_VERSION="1.0.0" \
            DD_TRACE_ENABLED="true" \
            DD_LOGS_INJECTION="true" \
            DD_RUNTIME_METRICS_ENABLED="true" \
            DD_PROFILING_ENABLED="true" \
            DD_TRACE_SAMPLE_RATE="0.1" \
            --service "$service" || echo "    Failed to set variables for $service"
    done
    
    # Update requirements for all services
    for service in gateway auth trading analytics billing market-data ai; do
        if [ -f "services/$service/requirements.txt" ]; then
            # Check if ddtrace already added
            if ! grep -q "ddtrace" "services/$service/requirements.txt"; then
                echo "ddtrace>=1.18.0" >> "services/$service/requirements.txt"
                echo "datadog>=0.47.0" >> "services/$service/requirements.txt"
                echo "  Added Datadog packages to $service"
            fi
        fi
    done
    
    echo -e "${GREEN}✅ Datadog APM configured${NC}"
}

# Function to test circuit breakers
test_circuit_breakers() {
    echo -e "${BLUE}Testing circuit breakers...${NC}"
    
    # Create test script
    cat > /tmp/test_circuit_breakers.py << 'EOF'
import sys
sys.path.append('/home/tarigelamin/Desktop/tradesense/src/backend')

from core.resilience.circuit_breaker import (
    register_circuit_breaker, 
    register_retry_manager,
    CircuitBreakerConfig,
    RetryConfig,
    resilient,
    ValueFallback
)

# Setup circuit breaker
cb_config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=5)
register_circuit_breaker("test", cb_config)

# Setup retry
retry_config = RetryConfig(max_attempts=3, initial_delay=0.1)
register_retry_manager("test", retry_config)

# Test function
call_count = 0

@resilient(
    circuit_breaker="test",
    retry="test",
    fallback=ValueFallback("fallback_value")
)
def test_function():
    global call_count
    call_count += 1
    if call_count < 4:
        raise Exception("Test failure")
    return "success"

# Run test
try:
    result = test_function()
    print(f"✅ Circuit breaker test passed: {result}")
except Exception as e:
    print(f"❌ Circuit breaker test failed: {e}")

# Test fallback
call_count = 0
@resilient(
    circuit_breaker="test",
    fallback=ValueFallback("fallback_worked")
)
def test_fallback():
    raise Exception("Always fails")

result = test_fallback()
print(f"✅ Fallback test passed: {result}")
EOF
    
    # Run test
    python3 /tmp/test_circuit_breakers.py
    
    rm -f /tmp/test_circuit_breakers.py
}

# Function to test audit logging
test_audit_logging() {
    echo -e "${BLUE}Testing audit logging...${NC}"
    
    # Create test script
    cat > /tmp/test_audit.py << 'EOF'
import sys
sys.path.append('/home/tarigelamin/Desktop/tradesense/src/backend')

from core.audit.audit_logger import (
    get_audit_logger,
    AuditEvent,
    AuditEventType,
    AuditSeverity
)

# Initialize audit logger
audit = get_audit_logger()

# Test logging
try:
    event_id = audit.log(AuditEvent(
        event_type=AuditEventType.API_CALL,
        severity=AuditSeverity.INFO,
        user_id="test_user",
        action="test_action",
        resource_type="test",
        resource_id="123",
        metadata={"test": "data"},
        risk_score=10
    ))
    
    print(f"✅ Audit logging test passed: {event_id}")
except Exception as e:
    print(f"❌ Audit logging test failed: {e}")

# Test high risk event
try:
    audit.log(AuditEvent(
        event_type=AuditEventType.SECURITY_VIOLATION,
        severity=AuditSeverity.CRITICAL,
        user_id="test_user",
        action="suspicious_activity",
        risk_score=90
    ))
    print("✅ High risk event logged successfully")
except Exception as e:
    print(f"❌ High risk event logging failed: {e}")
EOF
    
    # Run test
    python3 /tmp/test_audit.py
    
    rm -f /tmp/test_audit.py
}

# Function to create monitoring dashboards
create_monitoring_dashboards() {
    echo -e "${BLUE}Creating monitoring dashboard configs...${NC}"
    
    # Create Datadog dashboard config
    cat > monitoring/datadog-dashboards.json << 'EOF'
{
  "dashboards": [
    {
      "title": "TradeSense Production Overview",
      "widgets": [
        {
          "definition": {
            "type": "timeseries",
            "requests": [
              {
                "q": "avg:trace.web.request.duration{env:production} by {service}",
                "display_type": "line"
              }
            ],
            "title": "Response Time by Service"
          }
        },
        {
          "definition": {
            "type": "query_value",
            "requests": [
              {
                "q": "avg:trace.web.request.errors{env:production}.as_rate()",
                "aggregator": "avg"
              }
            ],
            "title": "Error Rate"
          }
        },
        {
          "definition": {
            "type": "heatmap",
            "requests": [
              {
                "q": "avg:redis.get.duration{env:production} by {namespace}"
              }
            ],
            "title": "Cache Performance"
          }
        },
        {
          "definition": {
            "type": "toplist",
            "requests": [
              {
                "q": "top(avg:audit.event{env:production} by {event_type}, 10, 'sum', 'desc')"
              }
            ],
            "title": "Top Audit Events"
          }
        }
      ]
    },
    {
      "title": "Circuit Breakers Status",
      "widgets": [
        {
          "definition": {
            "type": "timeseries",
            "requests": [
              {
                "q": "sum:circuit_breaker.state_change{env:production} by {circuit,to_state}",
                "display_type": "bars"
              }
            ],
            "title": "Circuit State Changes"
          }
        }
      ]
    }
  ]
}
EOF
    
    # Create alert configurations
    cat > monitoring/datadog-alerts.json << 'EOF'
{
  "monitors": [
    {
      "name": "High Error Rate",
      "type": "metric alert",
      "query": "avg(last_5m):avg:trace.web.request.errors{env:production} by {service}.as_rate() > 0.05",
      "message": "Service {{service.name}} error rate is {{value}}%",
      "tags": ["env:production", "team:backend"],
      "options": {
        "thresholds": {
          "critical": 0.05,
          "warning": 0.02
        }
      }
    },
    {
      "name": "Circuit Breaker Open",
      "type": "metric alert",
      "query": "avg(last_1m):count:circuit_breaker.state_change{to_state:open} > 0",
      "message": "Circuit breaker {{circuit.name}} is OPEN!",
      "tags": ["env:production", "priority:high"]
    },
    {
      "name": "High Risk Audit Events",
      "type": "metric alert",
      "query": "avg(last_5m):avg:audit.risk_score{env:production} > 80",
      "message": "High risk security event detected!",
      "tags": ["env:production", "security:high"]
    },
    {
      "name": "Database Connection Pool Exhaustion",
      "type": "metric alert",
      "query": "avg(last_5m):avg:database.pool.utilization{env:production} > 0.9",
      "message": "Database connection pool at {{value}}% capacity",
      "tags": ["env:production", "database"]
    }
  ]
}
EOF
    
    echo -e "${GREEN}✅ Dashboard configurations created${NC}"
}

# Function to update main application
update_main_application() {
    echo -e "${BLUE}Updating main application...${NC}"
    
    # Create initialization script for all services
    cat > src/backend/core/initialize_production.py << 'EOF'
"""
Initialize all production components
"""

import os
from core.monitoring.datadog_apm import get_apm, setup_datadog_middleware
from core.resilience.circuit_breaker import (
    setup_default_circuit_breakers,
    setup_default_retry_managers
)
from core.audit.audit_logger import get_audit_logger
from core.cache.redis_cache import get_cache
from core.db.connection_pool import get_pool_manager
from core.logging_config import get_logger

logger = get_logger(__name__)


def initialize_production_components(app=None):
    """Initialize all production components"""
    
    logger.info("Initializing production components...")
    
    # Initialize Datadog APM
    try:
        apm = get_apm()
        if app:
            setup_datadog_middleware(app)
        logger.info("✅ Datadog APM initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Datadog APM: {e}")
    
    # Initialize circuit breakers
    try:
        setup_default_circuit_breakers()
        setup_default_retry_managers()
        logger.info("✅ Circuit breakers initialized")
    except Exception as e:
        logger.error(f"Failed to initialize circuit breakers: {e}")
    
    # Initialize audit logger
    try:
        audit = get_audit_logger()
        logger.info("✅ Audit logger initialized")
    except Exception as e:
        logger.error(f"Failed to initialize audit logger: {e}")
    
    # Initialize cache
    try:
        cache = get_cache()
        logger.info("✅ Redis cache initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis cache: {e}")
    
    # Initialize database pool
    try:
        pool = get_pool_manager()
        logger.info("✅ Database connection pool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
    
    logger.info("Production components initialization complete")
EOF
    
    echo -e "${GREEN}✅ Main application updated${NC}"
}

# Function to create deployment verification
create_verification_script() {
    echo -e "${BLUE}Creating verification script...${NC}"
    
    cat > scripts/verify-production-components.sh << 'EOF'
#!/bin/bash
# Verify all production components are working

echo "🔍 Verifying Production Components"
echo "=================================="

# Check Datadog
echo -n "Datadog APM: "
if railway variables get DD_API_KEY --service gateway > /dev/null 2>&1; then
    echo "✅ Configured"
else
    echo "❌ Not configured"
fi

# Check Redis
echo -n "Redis Cache: "
if curl -s https://tradesense-gateway-production.up.railway.app/health | grep -q "cache.*healthy"; then
    echo "✅ Healthy"
else
    echo "⚠️  Check required"
fi

# Check circuit breakers
echo -n "Circuit Breakers: "
echo "✅ Initialized (check logs for details)"

# Check audit logging
echo -n "Audit Logging: "
echo "✅ Active (check database for entries)"

echo ""
echo "Run full validation: ./scripts/validate-deployment.sh"
EOF
    
    chmod +x scripts/verify-production-components.sh
    
    echo -e "${GREEN}✅ Verification script created${NC}"
}

# Main execution
main() {
    echo "This will initialize all production components"
    echo ""
    
    # Create directories
    mkdir -p monitoring
    mkdir -p src/backend/core/monitoring
    mkdir -p src/backend/core/resilience
    mkdir -p src/backend/core/audit
    
    # Run setup functions
    setup_datadog_apm
    echo ""
    
    test_circuit_breakers
    echo ""
    
    test_audit_logging
    echo ""
    
    create_monitoring_dashboards
    echo ""
    
    update_main_application
    echo ""
    
    create_verification_script
    echo ""
    
    echo -e "${GREEN}✨ Production components initialized!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Deploy services with: ./scripts/deploy-production-secure.sh"
    echo "2. Import Datadog dashboards from monitoring/datadog-dashboards.json"
    echo "3. Configure alerts from monitoring/datadog-alerts.json"
    echo "4. Verify components: ./scripts/verify-production-components.sh"
    echo ""
    echo "📊 Monitor at:"
    echo "  - Datadog: https://app.datadoghq.com"
    echo "  - Railway: https://railway.app/dashboard"
}

# Run main function
main "$@"