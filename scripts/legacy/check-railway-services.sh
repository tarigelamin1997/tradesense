#!/bin/bash

echo "🔍 Checking Railway Microservices Status"
echo "========================================"
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
    
    echo -n "Checking $name... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url/health" --max-time 5)
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ UP (200)${NC}"
        # Get detailed health
        curl -s "$url/health" | jq -c . 2>/dev/null || echo "No JSON response"
    elif [ "$response" = "000" ]; then
        echo -e "${YELLOW}⏳ Not deployed yet${NC}"
    else
        echo -e "${RED}❌ Down ($response)${NC}"
    fi
}

echo -e "${YELLOW}Core Services:${NC}"
check_service "Gateway" "https://tradesense-gateway.up.railway.app"
check_service "Auth" "https://tradesense-auth.up.railway.app"
check_service "Trading" "https://tradesense-trading.up.railway.app"

echo -e "\n${YELLOW}Additional Services (not deployed yet):${NC}"
check_service "Analytics" "https://tradesense-analytics.up.railway.app"
check_service "Market Data" "https://tradesense-market-data.up.railway.app"
check_service "Billing" "https://tradesense-billing.up.railway.app"
check_service "AI" "https://tradesense-ai.up.railway.app"

echo -e "\n${YELLOW}Project URLs:${NC}"
echo "Gateway: https://railway.com/project/e155abc9-0cd8-4c6f-b31d-572fa2548058"
echo "Auth: https://railway.com/project/c24752c8-ae7a-4577-9579-709ac623bea1"
echo "Trading: https://railway.com/project/20d52e60-bb93-485e-a6c1-44cc0ecc4715"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Add PostgreSQL databases to Auth and Trading projects"
echo "2. Set environment variables for each service"
echo "3. Wait for deployments to complete"
echo "4. Test the complete flow"