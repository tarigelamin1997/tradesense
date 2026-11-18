#!/bin/bash

# Test script for production endpoints
# This script tests various aspects of the production deployment

echo "==================================="
echo "TradeSense Production Endpoint Test"
echo "==================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Production URLs
GATEWAY_URL="${GATEWAY_URL:-https://tradesense-gateway.onrender.com}"
AUTH_URL="${AUTH_URL:-https://tradesense-auth.onrender.com}"
FRONTEND_URL="${FRONTEND_URL:-https://frontend-self-nu-47.vercel.app}"

echo "Testing with URLs:"
echo "Gateway: $GATEWAY_URL"
echo "Auth: $AUTH_URL"
echo "Frontend: $FRONTEND_URL"
echo ""

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    local data=$4
    local headers=$5
    
    echo -n "Testing $name... "
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X GET "$url" -H "Accept: application/json" $headers 2>/dev/null)
    elif [ "$method" == "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "Content-Type: application/x-www-form-urlencoded" \
            -H "Accept: application/json" \
            $headers \
            -d "$data" 2>/dev/null)
    elif [ "$method" == "OPTIONS" ]; then
        response=$(curl -s -w "\n%{http_code}" -X OPTIONS "$url" \
            -H "Origin: $FRONTEND_URL" \
            -H "Access-Control-Request-Method: POST" \
            -H "Access-Control-Request-Headers: content-type" \
            -i 2>/dev/null)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" == "200" ] || [ "$http_code" == "204" ]; then
        echo -e "${GREEN}✓${NC} (HTTP $http_code)"
        if [ "$method" == "OPTIONS" ]; then
            echo "$response" | grep -i "access-control" | head -5
        else
            echo "$body" | jq . 2>/dev/null || echo "$body"
        fi
    else
        echo -e "${RED}✗${NC} (HTTP $http_code)"
        echo "$body" | jq . 2>/dev/null || echo "$body"
    fi
    echo ""
}

# Test Gateway endpoints
echo "==================================="
echo "1. Testing Gateway Endpoints"
echo "==================================="
echo ""

test_endpoint "Gateway root" "$GATEWAY_URL/"
test_endpoint "Gateway health" "$GATEWAY_URL/health"
test_endpoint "Gateway services" "$GATEWAY_URL/services"
test_endpoint "Gateway metrics" "$GATEWAY_URL/metrics"

# Test Auth Service directly
echo "==================================="
echo "2. Testing Auth Service Directly"
echo "==================================="
echo ""

test_endpoint "Auth root" "$AUTH_URL/"
test_endpoint "Auth health" "$AUTH_URL/health"

# Test Gateway Auth routing
echo "==================================="
echo "3. Testing Auth via Gateway"
echo "==================================="
echo ""

test_endpoint "Auth via Gateway (/auth/token)" "$GATEWAY_URL/auth/token" "OPTIONS"
test_endpoint "Auth via Gateway (/api/auth/token)" "$GATEWAY_URL/api/auth/token" "OPTIONS"

# Test CORS preflight
echo "==================================="
echo "4. Testing CORS Preflight Requests"
echo "==================================="
echo ""

echo "Testing CORS for $GATEWAY_URL/auth/token from $FRONTEND_URL:"
curl -s -i -X OPTIONS "$GATEWAY_URL/auth/token" \
    -H "Origin: $FRONTEND_URL" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: content-type" | grep -i "access-control" | head -10
echo ""

# Test actual login attempt
echo "==================================="
echo "5. Testing Login Endpoint"
echo "==================================="
echo ""

echo "Testing login with test credentials:"
curl -s -X POST "$GATEWAY_URL/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "Origin: $FRONTEND_URL" \
    -H "Accept: application/json" \
    -d "username=test@example.com&password=testpassword" | jq . 2>/dev/null || echo "Failed to parse response"
echo ""

# Check DNS resolution
echo "==================================="
echo "6. DNS Resolution Check"
echo "==================================="
echo ""

for url in "$GATEWAY_URL" "$AUTH_URL"; do
    domain=$(echo $url | cut -d'/' -f3)
    echo -n "Resolving $domain... "
    if host $domain > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        host $domain | head -2
    else
        echo -e "${RED}✗${NC}"
    fi
    echo ""
done

# Test connectivity from different methods
echo "==================================="
echo "7. Testing Different Request Methods"
echo "==================================="
echo ""

echo "Testing with curl (direct):"
curl -s -o /dev/null -w "Gateway: %{http_code}\n" "$GATEWAY_URL/health"
curl -s -o /dev/null -w "Auth: %{http_code}\n" "$AUTH_URL/health"
echo ""

echo "Testing with wget:"
wget -q -O /dev/null --server-response "$GATEWAY_URL/health" 2>&1 | grep "HTTP/" | tail -1
wget -q -O /dev/null --server-response "$AUTH_URL/health" 2>&1 | grep "HTTP/" | tail -1
echo ""

# Summary
echo "==================================="
echo "8. Summary and Recommendations"
echo "==================================="
echo ""

echo "Based on the tests above:"
echo ""
echo "1. Check if all services show 'healthy' status"
echo "2. Verify CORS headers are present and include your frontend URL"
echo "3. Ensure auth endpoints are accessible via gateway"
echo "4. Check for any 502/503 errors indicating service communication issues"
echo ""
echo "Common issues and fixes:"
echo "- 502/503: Service is down or not reachable"
echo "- 404: Routing issue in gateway"
echo "- CORS errors: Frontend URL not in allowed origins"
echo "- Connection refused: Service not running or wrong port"
echo ""

echo "Frontend should use: $GATEWAY_URL for all API calls"
echo "Environment variable in frontend: VITE_API_BASE_URL=$GATEWAY_URL"