#!/bin/bash
# Production Health Monitoring Script for TradeSense
# Monitors all services and provides real-time status

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service URLs (update with your actual URLs)
GATEWAY_URL="${GATEWAY_URL:-https://tradesense-gateway-production.up.railway.app}"
AUTH_URL="${AUTH_URL:-https://tradesense-auth-production.up.railway.app}"
TRADING_URL="${TRADING_URL:-https://tradesense-trading-production.up.railway.app}"
ANALYTICS_URL="${ANALYTICS_URL:-https://tradesense-analytics-production.up.railway.app}"
BILLING_URL="${BILLING_URL:-https://tradesense-billing-production.up.railway.app}"
MARKET_DATA_URL="${MARKET_DATA_URL:-https://tradesense-market-data-production.up.railway.app}"
AI_URL="${AI_URL:-https://tradesense-ai-production.up.railway.app}"
FRONTEND_URL="${FRONTEND_URL:-https://tradesense.vercel.app}"

# Function to check service health
check_service() {
    local name=$1
    local url=$2
    local start_time=$(date +%s%N)
    
    # Make request with timeout
    if response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$url/health" 2>/dev/null); then
        local end_time=$(date +%s%N)
        local response_time=$(( ($end_time - $start_time) / 1000000 )) # Convert to milliseconds
        
        if [ "$response" = "200" ]; then
            echo -e "${GREEN}✅ $name${NC} - Healthy (${response_time}ms)"
            return 0
        else
            echo -e "${YELLOW}⚠️  $name${NC} - Unhealthy (HTTP $response)"
            return 1
        fi
    else
        echo -e "${RED}❌ $name${NC} - Unreachable"
        return 1
    fi
}

# Function to check database connectivity
check_database() {
    local service=$1
    local url=$2
    
    if response=$(curl -s --connect-timeout 5 --max-time 10 "$url/health/db" 2>/dev/null); then
        if echo "$response" | grep -q "healthy"; then
            echo -e "  └─ Database: ${GREEN}Connected${NC}"
        else
            echo -e "  └─ Database: ${RED}Disconnected${NC}"
        fi
    fi
}

# Function to get service metrics
get_metrics() {
    local url=$1
    
    if metrics=$(curl -s --connect-timeout 5 --max-time 10 "$url/metrics" 2>/dev/null); then
        # Parse key metrics
        local requests=$(echo "$metrics" | grep "http_requests_total" | tail -1 | awk '{print $2}' || echo "0")
        local errors=$(echo "$metrics" | grep "http_requests_failed_total" | tail -1 | awk '{print $2}' || echo "0")
        local latency=$(echo "$metrics" | grep "http_request_duration_seconds" | grep "0.99" | awk '{print $2}' || echo "0")
        
        echo -e "  └─ Metrics: Requests: $requests | Errors: $errors | P99 Latency: ${latency}s"
    fi
}

# Main monitoring loop
monitor_services() {
    clear
    echo "🏥 TradeSense Production Health Monitor"
    echo "======================================"
    echo "Time: $(date)"
    echo ""
    
    local total_services=8
    local healthy_services=0
    
    # Check each service
    echo "📊 Service Status:"
    echo ""
    
    # Gateway
    if check_service "Gateway" "$GATEWAY_URL"; then
        ((healthy_services++))
        check_database "Gateway" "$GATEWAY_URL"
        get_metrics "$GATEWAY_URL"
    fi
    echo ""
    
    # Auth
    if check_service "Auth Service" "$AUTH_URL"; then
        ((healthy_services++))
        check_database "Auth" "$AUTH_URL"
    fi
    echo ""
    
    # Trading
    if check_service "Trading Service" "$TRADING_URL"; then
        ((healthy_services++))
        check_database "Trading" "$TRADING_URL"
    fi
    echo ""
    
    # Analytics
    if check_service "Analytics Service" "$ANALYTICS_URL"; then
        ((healthy_services++))
        check_database "Analytics" "$ANALYTICS_URL"
    fi
    echo ""
    
    # Billing
    if check_service "Billing Service" "$BILLING_URL"; then
        ((healthy_services++))
    fi
    echo ""
    
    # Market Data
    if check_service "Market Data Service" "$MARKET_DATA_URL"; then
        ((healthy_services++))
    fi
    echo ""
    
    # AI
    if check_service "AI Service" "$AI_URL"; then
        ((healthy_services++))
    fi
    echo ""
    
    # Frontend
    if check_service "Frontend (Vercel)" "$FRONTEND_URL"; then
        ((healthy_services++))
    fi
    echo ""
    
    # Overall status
    echo "======================================"
    if [ $healthy_services -eq $total_services ]; then
        echo -e "${GREEN}✅ System Status: HEALTHY${NC} ($healthy_services/$total_services services operational)"
    elif [ $healthy_services -ge $((total_services - 2)) ]; then
        echo -e "${YELLOW}⚠️  System Status: DEGRADED${NC} ($healthy_services/$total_services services operational)"
    else
        echo -e "${RED}❌ System Status: CRITICAL${NC} ($healthy_services/$total_services services operational)"
    fi
    echo ""
    
    # Additional checks
    echo "🔍 Additional Checks:"
    
    # Check API Gateway routing
    echo -n "  • API Gateway Routing: "
    if curl -s -f "$GATEWAY_URL/api/v1/auth/health" > /dev/null 2>&1; then
        echo -e "${GREEN}Working${NC}"
    else
        echo -e "${RED}Failed${NC}"
    fi
    
    # Check CORS
    echo -n "  • CORS Configuration: "
    if curl -s -I -H "Origin: https://tradesense.ai" "$GATEWAY_URL/health" 2>/dev/null | grep -q "access-control-allow-origin"; then
        echo -e "${GREEN}Properly configured${NC}"
    else
        echo -e "${YELLOW}May need adjustment${NC}"
    fi
    
    # Check SSL
    echo -n "  • SSL Certificates: "
    for url in "$GATEWAY_URL" "$FRONTEND_URL"; do
        if curl -s -I "$url" 2>&1 | grep -q "SSL certificate problem"; then
            echo -e "${RED}Invalid${NC}"
            break
        fi
    done
    echo -e "${GREEN}Valid${NC}"
    
    echo ""
    echo "======================================"
    echo "Press Ctrl+C to exit | Refreshing in 30s..."
}

# Create detailed health report
generate_report() {
    local report_file="health-report-$(date +%Y%m%d-%H%M%S).json"
    
    echo "{" > "$report_file"
    echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"," >> "$report_file"
    echo "  \"services\": {" >> "$report_file"
    
    # Check each service and add to report
    for service in "gateway:$GATEWAY_URL" "auth:$AUTH_URL" "trading:$TRADING_URL" "analytics:$ANALYTICS_URL"; do
        IFS=':' read -r name url <<< "$service"
        
        local status="down"
        local response_time=0
        
        local start_time=$(date +%s%N)
        if curl -s -f "$url/health" > /dev/null 2>&1; then
            status="up"
            local end_time=$(date +%s%N)
            response_time=$(( ($end_time - $start_time) / 1000000 ))
        fi
        
        echo "    \"$name\": {" >> "$report_file"
        echo "      \"status\": \"$status\"," >> "$report_file"
        echo "      \"response_time_ms\": $response_time," >> "$report_file"
        echo "      \"url\": \"$url\"" >> "$report_file"
        echo "    }," >> "$report_file"
    done
    
    # Remove trailing comma and close JSON
    sed -i '$ s/,$//' "$report_file"
    echo "  }" >> "$report_file"
    echo "}" >> "$report_file"
    
    echo "📄 Health report saved to: $report_file"
}

# Main execution
case "${1:-monitor}" in
    "monitor")
        # Continuous monitoring
        while true; do
            monitor_services
            sleep 30
        done
        ;;
    "check")
        # Single check
        monitor_services
        ;;
    "report")
        # Generate report
        generate_report
        ;;
    *)
        echo "Usage: $0 [monitor|check|report]"
        echo "  monitor - Continuous monitoring (default)"
        echo "  check   - Single health check"
        echo "  report  - Generate health report"
        exit 1
        ;;
esac