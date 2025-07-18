#!/bin/bash

echo "👀 Watching Railway Deployment"
echo "============================="
echo "Build URL: https://railway.com/project/08df85d3-c89a-4082-887b-8361569a01f3/service/7be4cb72-a5da-4f3c-aec2-909357c08518"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to check endpoint
check_endpoint() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" https://tradesense-production.up.railway.app/health 2>/dev/null)
    echo "$response"
}

# Monitor deployment
echo "Monitoring deployment status..."
echo "Press Ctrl+C to stop"
echo ""

attempt=0
while true; do
    attempt=$((attempt + 1))
    status=$(check_endpoint)
    
    timestamp=$(date '+%H:%M:%S')
    
    if [ "$status" = "200" ]; then
        echo -e "${timestamp} - ${GREEN}✅ Backend is UP!${NC} (HTTP $status)"
        echo "Testing endpoints:"
        echo -n "  /health: "
        curl -s https://tradesense-production.up.railway.app/health | jq -c .
        echo -n "  /api: "
        curl -s https://tradesense-production.up.railway.app/api | jq -c .
        echo ""
        echo "🎉 Deployment successful!"
        echo "Backend URL: https://tradesense-production.up.railway.app"
        break
    else
        echo -e "${timestamp} - ${YELLOW}⏳ Waiting...${NC} (attempt $attempt, status: $status)"
    fi
    
    sleep 5
done