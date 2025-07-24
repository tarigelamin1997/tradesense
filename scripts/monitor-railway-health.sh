#!/bin/bash

# Railway Health Monitoring Script
# Real-time health monitoring for all Railway services

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Service configuration
declare -A SERVICES=(
    ["Gateway"]="https://tradesense-gateway-production.up.railway.app"
    ["Auth"]="https://tradesense-auth-production.up.railway.app"
    ["Trading"]="https://tradesense-trading-production.up.railway.app"
    ["Analytics"]="https://tradesense-analytics-production.up.railway.app"
    ["Market Data"]="https://tradesense-market-data-production.up.railway.app"
    ["Billing"]="https://tradesense-billing-production.up.railway.app"
    ["AI"]="https://tradesense-ai-production.up.railway.app"
)

# Monitoring configuration
INTERVAL=${1:-15}  # Default 15 seconds
LOG_FILE="railway-health-$(date +%Y%m%d).log"
SLACK_WEBHOOK=${SLACK_WEBHOOK_URL:-""}
ALERT_THRESHOLD=3  # Number of failures before alerting

# Track failures
declare -A FAILURE_COUNT
declare -A LAST_STATUS
declare -A RESPONSE_TIMES

# Initialize
for service in "${!SERVICES[@]}"; do
    FAILURE_COUNT["$service"]=0
    LAST_STATUS["$service"]="unknown"
    RESPONSE_TIMES["$service"]=0
done

# Functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_alert() {
    local service=$1
    local status=$2
    local message=$3
    
    log "ALERT: $service is $status - $message"
    
    # Send to Slack if webhook is configured
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{
                \"text\": \"🚨 Railway Service Alert\",
                \"attachments\": [{
                    \"color\": \"danger\",
                    \"fields\": [
                        {\"title\": \"Service\", \"value\": \"$service\", \"short\": true},
                        {\"title\": \"Status\", \"value\": \"$status\", \"short\": true},
                        {\"title\": \"Message\", \"value\": \"$message\"},
                        {\"title\": \"Time\", \"value\": \"$(date)\"}
                    ]
                }]
            }" 2>/dev/null
    fi
}

check_service() {
    local name=$1
    local url=$2
    local start_time=$(date +%s.%N)
    
    # Make health check request
    response=$(curl -s -w "\n%{http_code}\n%{time_total}" -o /tmp/health_response_$$ "${url}/health" --max-time 10 2>/dev/null) || echo -e "\n000\n0"
    
    # Parse response
    status_code=$(echo "$response" | tail -2 | head -1)
    response_time=$(echo "$response" | tail -1)
    response_time_ms=$(echo "$response_time * 1000" | bc | cut -d. -f1)
    
    # Read JSON response
    if [[ -f /tmp/health_response_$$ ]]; then
        json_response=$(cat /tmp/health_response_$$ 2>/dev/null | jq -c . 2>/dev/null || echo "{}")
        rm -f /tmp/health_response_$$
    else
        json_response="{}"
    fi
    
    # Update response time tracking
    RESPONSE_TIMES["$name"]=$response_time_ms
    
    # Check status
    if [[ "$status_code" == "200" ]]; then
        # Service is healthy
        if [[ "${LAST_STATUS[$name]}" != "healthy" ]]; then
            if [[ "${LAST_STATUS[$name]}" != "unknown" ]]; then
                send_alert "$name" "RECOVERED" "Service is back online after ${FAILURE_COUNT[$name]} failures"
            fi
        fi
        FAILURE_COUNT["$name"]=0
        LAST_STATUS["$name"]="healthy"
        
        # Parse health details
        db_status=$(echo "$json_response" | jq -r '.database // "unknown"' 2>/dev/null)
        
        echo -e "${GREEN}✅${NC} $name ${GREEN}HEALTHY${NC} (${response_time_ms}ms) DB: $db_status"
        
    elif [[ "$status_code" == "000" ]]; then
        # Timeout or connection error
        FAILURE_COUNT["$name"]=$((FAILURE_COUNT["$name"] + 1))
        LAST_STATUS["$name"]="timeout"
        
        echo -e "${RED}❌${NC} $name ${RED}TIMEOUT${NC}"
        
        if [[ ${FAILURE_COUNT["$name"]} -ge $ALERT_THRESHOLD ]]; then
            send_alert "$name" "DOWN" "Service timeout after ${FAILURE_COUNT[$name]} attempts"
        fi
        
    else
        # HTTP error
        FAILURE_COUNT["$name"]=$((FAILURE_COUNT["$name"] + 1))
        LAST_STATUS["$name"]="error"
        
        echo -e "${RED}❌${NC} $name ${RED}ERROR${NC} (HTTP $status_code)"
        
        if [[ ${FAILURE_COUNT["$name"]} -ge $ALERT_THRESHOLD ]]; then
            send_alert "$name" "ERROR" "HTTP $status_code after ${FAILURE_COUNT[$name]} attempts"
        fi
    fi
}

show_dashboard() {
    clear
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║              Railway Services Health Monitor                  ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "Monitoring Interval: ${YELLOW}${INTERVAL}s${NC} | Press ${RED}Ctrl+C${NC} to stop"
    echo -e "Time: $(date +'%Y-%m-%d %H:%M:%S')"
    echo ""
    echo -e "${BLUE}Service Status:${NC}"
    echo "────────────────────────────────────────────────────────────────"
}

show_summary() {
    echo ""
    echo "────────────────────────────────────────────────────────────────"
    echo -e "${BLUE}Summary:${NC}"
    
    # Count healthy services
    healthy_count=0
    total_response_time=0
    
    for service in "${!SERVICES[@]}"; do
        if [[ "${LAST_STATUS[$service]}" == "healthy" ]]; then
            healthy_count=$((healthy_count + 1))
        fi
        total_response_time=$((total_response_time + RESPONSE_TIMES[$service]))
    done
    
    avg_response_time=$((total_response_time / ${#SERVICES[@]}))
    
    echo -e "Healthy Services: ${GREEN}${healthy_count}${NC}/${#SERVICES[@]}"
    echo -e "Average Response Time: ${YELLOW}${avg_response_time}ms${NC}"
    
    # Show alerts if any
    alert_count=0
    for service in "${!SERVICES[@]}"; do
        if [[ ${FAILURE_COUNT[$service]} -gt 0 ]]; then
            alert_count=$((alert_count + 1))
        fi
    done
    
    if [[ $alert_count -gt 0 ]]; then
        echo -e "Active Alerts: ${RED}${alert_count}${NC}"
    fi
}

# Trap for cleanup
cleanup() {
    echo ""
    log "Monitoring stopped"
    exit 0
}

trap cleanup INT TERM

# Main monitoring loop
main() {
    log "Starting Railway health monitoring (interval: ${INTERVAL}s)"
    
    while true; do
        show_dashboard
        
        # Check all services
        for service in "${!SERVICES[@]}"; do
            check_service "$service" "${SERVICES[$service]}"
        done
        
        show_summary
        
        # Wait for next interval
        sleep "$INTERVAL"
    done
}

# Start monitoring
main