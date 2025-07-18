#!/bin/bash

echo "📊 Railway Deployment Monitor"
echo "============================"
echo "Checking every 30 seconds..."
echo "Press Ctrl+C to stop"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to check service
check_service() {
    local name=$1
    local url=$2
    local project=$3
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 5)
    
    if [ "$response" = "200" ]; then
        echo -e "$name: ${GREEN}✅ UP${NC} | $project"
    elif [ "$response" = "404" ]; then
        echo -e "$name: ${YELLOW}⏳ Building${NC} | $project"
    else
        echo -e "$name: ${RED}❌ Error ($response)${NC} | $project"
    fi
}

while true; do
    clear
    echo "📊 Railway Deployment Monitor"
    echo "============================"
    echo "Time: $(date)"
    echo ""
    
    echo "Core Services:"
    check_service "Gateway" \
        "https://tradesense-gateway-production.up.railway.app/health" \
        "https://railway.com/project/e155abc9-0cd8-4c6f-b31d-572fa2548058"
    
    check_service "Auth" \
        "https://tradesense-auth-production.up.railway.app/health" \
        "https://railway.com/project/c24752c8-ae7a-4577-9579-709ac623bea1"
    
    check_service "Trading" \
        "https://tradesense-trading-production.up.railway.app/health" \
        "https://railway.com/project/20d52e60-bb93-485e-a6c1-44cc0ecc4715"
    
    check_service "Analytics" \
        "https://tradesense-analytics-production.up.railway.app/health" \
        "https://railway.com/project/340578fb-7187-4c75-bf38-1adb4d85a1a8"
    
    echo ""
    echo "Configuration Checklist:"
    echo "[ ] Gateway - Add service URLs as env vars"
    echo "[ ] Auth - Add PostgreSQL + JWT_SECRET_KEY"
    echo "[ ] Trading - Add PostgreSQL + AUTH_SERVICE_URL"
    echo "[ ] Analytics - Add PostgreSQL + service URLs"
    
    echo ""
    echo "Once services are UP:"
    echo "1. Configure databases and env vars"
    echo "2. Run: ./test-railway-flow.sh"
    
    sleep 30
done