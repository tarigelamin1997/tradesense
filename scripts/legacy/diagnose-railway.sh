#!/bin/bash

echo "🔍 Railway Backend Diagnostics"
echo "============================="

# Check basic connectivity
echo -e "\n1. Testing backend URL..."
BACKEND_URL="https://tradesense-production.up.railway.app"

# Test health endpoint
echo "   - Health endpoint:"
curl -s "$BACKEND_URL/api/health" | python3 -m json.tool 2>/dev/null || echo "   ❌ Health check failed"

# Test root endpoint
echo -e "\n   - Root endpoint:"
curl -s "$BACKEND_URL/" -w "\n   HTTP Status: %{http_code}\n" -o /dev/null

# Check if it's a Railway issue
echo -e "\n2. Railway Status:"
echo "   - Check https://status.railway.app for any incidents"

echo -e "\n3. Common Railway Issues to Check:"
echo "   ❌ Missing environment variables (especially JWT_SECRET_KEY)"
echo "   ❌ Database connection timeout"
echo "   ❌ Import errors in Python code"
echo "   ❌ Port binding issues"
echo "   ❌ Memory/resource limits"

echo -e "\n4. To View Logs:"
echo "   Option 1: Railway Dashboard"
echo "   - Go to https://railway.app/dashboard"
echo "   - Click on your project"
echo "   - Click on the service"
echo "   - View deployment logs"
echo ""
echo "   Option 2: Railway CLI"
echo "   railway logs --tail 100"

echo -e "\n5. Quick Fixes:"
echo "   - Restart service: railway restart"
echo "   - Redeploy: railway up --detach"
echo "   - Check variables: railway variables"