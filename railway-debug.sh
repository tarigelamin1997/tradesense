#!/bin/bash

echo "🔍 Railway Debugging Script"
echo "=========================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "\n${BLUE}1. Checking Railway Status:${NC}"
railway status

echo -e "\n${BLUE}2. Checking Environment Variables:${NC}"
echo "Showing first few variables (sensitive data hidden)..."
railway variables | head -10

echo -e "\n${BLUE}3. Recent Deployment Status:${NC}"
# Try to get deployment info
railway deployments 2>&1 || echo "No deployment command available"

echo -e "\n${BLUE}4. Checking if databases are connected:${NC}"
railway variables | grep -E "(DATABASE_URL|REDIS_URL)" > /dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database URLs found in environment${NC}"
else
    echo -e "${RED}❌ Database URLs NOT found!${NC}"
    echo -e "${YELLOW}You need to connect PostgreSQL and Redis in Railway dashboard${NC}"
fi

echo -e "\n${BLUE}5. Quick fixes to try:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Force redeploy:"
echo "   railway up --detach"
echo ""
echo "2. Check Railway dashboard for build logs:"
echo "   https://railway.app/dashboard"
echo ""
echo "3. Ensure databases are connected:"
echo "   - Go to Railway dashboard"
echo "   - Click on your service"
echo "   - Go to Variables tab"
echo "   - Check for DATABASE_URL and REDIS_URL"
echo ""
echo "4. If databases are missing, add them:"
echo "   - Click 'New' → 'Database' → 'Add PostgreSQL'"
echo "   - Click 'New' → 'Database' → 'Add Redis'"
echo "   - Connect them to your service"

echo -e "\n${YELLOW}6. Common issues:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "❓ Application failed to respond = Usually means:"
echo "   - App crashed during startup"
echo "   - Missing environment variables"
echo "   - Database connection failed"
echo "   - Port binding issues"

echo -e "\n${BLUE}Done!${NC}"