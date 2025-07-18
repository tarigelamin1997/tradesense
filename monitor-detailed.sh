#!/bin/bash

echo "📊 Detailed Railway Monitor"
echo "========================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Service URLs
declare -A services=(
    ["Gateway"]="https://tradesense-gateway-production.up.railway.app"
    ["Auth"]="https://tradesense-auth-production.up.railway.app"
    ["Trading"]="https://tradesense-trading-production.up.railway.app"
    ["Analytics"]="https://tradesense-analytics-production.up.railway.app"
    ["Market-Data"]="https://tradesense-market-data-production.up.railway.app"
    ["Billing"]="https://tradesense-billing-production.up.railway.app"
    ["AI"]="https://tradesense-ai-production.up.railway.app"
)

# Check individual service
check_service() {
    local name=$1
    local url=$2
    
    # Check health endpoint
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$url/health" --max-time 5)
    
    # Extract status code
    http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    
    # Extract body
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    if [ "$http_code" = "200" ]; then
        # Try to parse JSON
        if echo "$body" | jq . >/dev/null 2>&1; then
            status=$(echo "$body" | jq -r .status 2>/dev/null || echo "unknown")
            db_status=$(echo "$body" | jq -r .database 2>/dev/null || echo "N/A")
            
            echo -e "${name}: ${GREEN}✅ UP${NC}"
            echo -e "  Status: $status"
            echo -e "  Database: $db_status"
            
            # Special handling for Gateway
            if [ "$name" = "Gateway" ]; then
                echo -e "  ${BLUE}Service Health:${NC}"
                echo "$body" | jq -r '.services | to_entries[] | "    \(.key): \(.value.status)"' 2>/dev/null || echo "    Unable to parse services"
            fi
        else
            echo -e "${name}: ${GREEN}✅ UP${NC} (non-JSON response)"
        fi
    elif [ "$http_code" = "404" ]; then
        echo -e "${name}: ${YELLOW}🔨 Building/Deploying${NC}"
    elif [ "$http_code" = "502" ] || [ "$http_code" = "503" ]; then
        echo -e "${name}: ${RED}❌ Service Error${NC}"
    else
        echo -e "${name}: ${RED}⚠️  Unknown ($http_code)${NC}"
    fi
    echo ""
}

# Main monitoring loop
while true; do
    clear
    echo "📊 Detailed Railway Monitor"
    echo "========================="
    echo "Time: $(date)"
    echo ""
    
    # Check each service
    for service in Gateway Auth Trading Analytics Market-Data Billing AI; do
        check_service "$service" "${services[$service]}"
    done
    
    echo "========================="
    echo "Configuration Status:"
    echo ""
    echo "✅ Configured = Service is UP with healthy database"
    echo "🔨 Building = Service is deploying"
    echo "❌ Error = Check Railway logs"
    echo ""
    echo "Press Ctrl+C to stop"
    
    sleep 15
done