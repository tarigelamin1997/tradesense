#!/bin/bash

echo "🧪 Testing TradeSense Microservices"
echo "==================================="

BASE_URL="http://localhost:8000/api"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${YELLOW}1. Testing Gateway Health${NC}"
curl -s http://localhost:8000/health | jq .

echo -e "\n${YELLOW}2. Registering a new user${NC}"
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123"
  }')

echo $REGISTER_RESPONSE | jq .

echo -e "\n${YELLOW}3. Logging in${NC}"
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123")

echo $LOGIN_RESPONSE | jq .

# Extract token
TOKEN=$(echo $LOGIN_RESPONSE | jq -r .access_token)

if [ "$TOKEN" != "null" ]; then
  echo -e "\n${GREEN}✅ Login successful! Token: ${TOKEN:0:20}...${NC}"
  
  echo -e "\n${YELLOW}4. Getting user info${NC}"
  curl -s $BASE_URL/auth/me \
    -H "Authorization: Bearer $TOKEN" | jq .
  
  echo -e "\n${YELLOW}5. Creating a trade${NC}"
  TRADE_RESPONSE=$(curl -s -X POST $BASE_URL/trades \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "symbol": "AAPL",
      "action": "buy",
      "quantity": 10,
      "price": 150.50
    }')
  
  echo $TRADE_RESPONSE | jq .
  
  echo -e "\n${YELLOW}6. Getting portfolio${NC}"
  curl -s $BASE_URL/portfolio \
    -H "Authorization: Bearer $TOKEN" | jq .
  
  echo -e "\n${YELLOW}7. Getting trades${NC}"
  curl -s $BASE_URL/trades \
    -H "Authorization: Bearer $TOKEN" | jq .
    
  echo -e "\n${GREEN}✅ All tests passed!${NC}"
else
  echo -e "\n${RED}❌ Login failed${NC}"
fi