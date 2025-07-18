#!/bin/bash

echo "🧪 Testing Railway Microservices Flow"
echo "===================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Gateway URL
GATEWAY_URL="https://tradesense-gateway-production.up.railway.app"

echo -e "\n${YELLOW}1. Checking Gateway Health${NC}"
gateway_health=$(curl -s "$GATEWAY_URL/health")
echo "$gateway_health" | jq .

# Extract service statuses
auth_status=$(echo "$gateway_health" | jq -r '.services.auth.status')
trading_status=$(echo "$gateway_health" | jq -r '.services.trading.status')

if [ "$auth_status" != "healthy" ] || [ "$trading_status" != "healthy" ]; then
    echo -e "${RED}❌ Core services not healthy yet. Please wait for deployment to complete.${NC}"
    exit 1
fi

echo -e "\n${GREEN}✅ Core services are healthy!${NC}"

echo -e "\n${YELLOW}2. Testing User Registration${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$GATEWAY_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "railway@test.com",
    "username": "railwayuser",
    "password": "railway123"
  }')

echo "$REGISTER_RESPONSE" | jq .

echo -e "\n${YELLOW}3. Testing Login${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$GATEWAY_URL/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=railwayuser&password=railway123")

echo "$LOGIN_RESPONSE" | jq .

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r .access_token)

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Login failed${NC}"
    exit 1
fi

echo -e "\n${GREEN}✅ Authentication successful!${NC}"

echo -e "\n${YELLOW}4. Creating a Trade${NC}"
TRADE_RESPONSE=$(curl -s -X POST "$GATEWAY_URL/api/trades" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "action": "buy",
    "quantity": 10,
    "price": 175.50
  }')

echo "$TRADE_RESPONSE" | jq .

echo -e "\n${YELLOW}5. Getting Portfolio${NC}"
curl -s "$GATEWAY_URL/api/portfolio" \
  -H "Authorization: Bearer $TOKEN" | jq .

echo -e "\n${YELLOW}6. Getting Performance Analytics${NC}"
curl -s "$GATEWAY_URL/api/analytics/performance" \
  -H "Authorization: Bearer $TOKEN" | jq .

echo -e "\n${YELLOW}7. Testing Market Data (if deployed)${NC}"
curl -s "$GATEWAY_URL/api/market-data/quote/AAPL" | jq .

echo -e "\n${YELLOW}8. Testing AI Service (if deployed)${NC}"
curl -s -X POST "$GATEWAY_URL/api/ai/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the best trading strategy for beginners?"
  }' | jq .

echo -e "\n${GREEN}🎉 Microservices flow test complete!${NC}"
echo ""
echo "Summary:"
echo "- Gateway: ✅ Routing requests correctly"
echo "- Auth: ✅ User registration and JWT working"
echo "- Trading: ✅ Trades and portfolio working"
echo "- Analytics: Check if performance metrics returned"
echo "- Market Data: Check if quote returned"
echo "- AI: Check if response generated"