#!/bin/bash

# Gateway Route Verification Script
# Checks if all expected routes are available

echo "🔍 Gateway Route Verification"
echo "============================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

GATEWAY_URL="https://tradesense-gateway-production.up.railway.app"

# Test function
test_route() {
    local method=$1
    local path=$2
    local expected=$3
    local data=$4
    
    echo -n "Testing $method $path: "
    
    if [ -n "$data" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$GATEWAY_URL$path" -H "Content-Type: application/x-www-form-urlencoded" -d "$data")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$GATEWAY_URL$path")
    fi
    
    if [ "$response" = "$expected" ]; then
        echo -e "${GREEN}✅ Pass (HTTP $response)${NC}"
        return 0
    else
        echo -e "${RED}❌ Fail (Expected $expected, got $response)${NC}"
        return 1
    fi
}

# Track failures
FAILURES=0

echo -e "${BLUE}Core Gateway Routes:${NC}"
echo "--------------------"
test_route "GET" "/" "200" || ((FAILURES++))
test_route "GET" "/health" "200" || ((FAILURES++))
test_route "GET" "/services" "200" || ((FAILURES++))

echo ""
echo -e "${BLUE}Auth Service Routes (Direct):${NC}"
echo "-----------------------------"
test_route "POST" "/auth/token" "401" "username=test&password=test" || ((FAILURES++))
test_route "POST" "/auth/register" "422" "" || ((FAILURES++))
test_route "GET" "/auth/me" "401" || ((FAILURES++))

echo ""
echo -e "${BLUE}Auth Service Routes (API Prefix):${NC}"
echo "---------------------------------"
test_route "POST" "/api/auth/token" "401" "username=test&password=test" || ((FAILURES++))
test_route "POST" "/api/auth/register" "422" "" || ((FAILURES++))
test_route "GET" "/api/auth/me" "401" || ((FAILURES++))

echo ""
echo -e "${BLUE}Other Service Routes:${NC}"
echo "---------------------"
test_route "GET" "/api/trades" "401" || ((FAILURES++))
test_route "GET" "/api/analytics/dashboard" "401" || ((FAILURES++))
test_route "GET" "/api/market-data/quotes" "401" || ((FAILURES++))

echo ""
echo -e "${BLUE}Service Health Status:${NC}"
echo "---------------------"
health_data=$(curl -s "$GATEWAY_URL/health" 2>/dev/null | jq -r '.services | to_entries[] | "\(.key): \(.value.status)"' 2>/dev/null || echo "Failed to fetch")
echo "$health_data"

echo ""
echo "============================"
echo -e "${BLUE}Verification Summary${NC}"
echo "============================"

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ All routes working correctly!${NC}"
    echo ""
    echo "The gateway is properly configured and routing requests."
else
    echo -e "${RED}❌ $FAILURES route(s) failed${NC}"
    echo ""
    
    # Check specific auth route issue
    auth_direct=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$GATEWAY_URL/auth/token" -d "username=test&password=test")
    auth_api=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$GATEWAY_URL/api/auth/token" -d "username=test&password=test")
    
    if [ "$auth_direct" = "404" ] && [ "$auth_api" = "401" ]; then
        echo -e "${YELLOW}Issue: Direct auth routes (/auth/*) not configured${NC}"
        echo "The gateway only responds to /api/* prefixed routes"
        echo ""
        echo "Solution: The gateway needs the direct auth route handler deployed"
    elif [ "$auth_direct" = "404" ] && [ "$auth_api" = "404" ]; then
        echo -e "${RED}Issue: Gateway not routing to auth service at all${NC}"
        echo "Both direct and API routes are returning 404"
        echo ""
        echo "Solution: Check gateway deployment and service configuration"
    fi
fi

echo ""
echo -e "${BLUE}Current Gateway Configuration:${NC}"
echo "------------------------------"
services=$(curl -s "$GATEWAY_URL/services" 2>/dev/null | jq -r '.services.auth.url' 2>/dev/null || echo "Unable to fetch")
echo "Auth Service URL: $services"

echo ""
echo -e "${BLUE}Recommendations:${NC}"
echo "----------------"

if [ "$auth_direct" = "404" ]; then
    echo "1. Run: ./scripts/force-gateway-deployment.sh"
    echo "2. Or manually redeploy gateway in Railway with cache cleared"
    echo "3. Ensure gateway code includes direct auth route handlers"
else
    echo "1. Update frontend to use gateway URL"
    echo "2. Remove direct auth service connection"
    echo "3. Test authentication flow end-to-end"
fi