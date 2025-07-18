#!/bin/bash

# Railway Status Check Script
# Monitors deployment status and health

echo "🔍 Railway Status Check"
echo "======================"

# Check if Railway CLI is logged in
if ! railway whoami &>/dev/null; then
    echo "❌ Not logged into Railway CLI"
    echo "Run: railway login"
    exit 1
fi

# Get deployment URL
echo -e "\n🌐 Getting deployment URL..."
DEPLOY_URL=$(railway status --json 2>/dev/null | grep -o '"url":"[^"]*' | grep -o '[^"]*$' || echo "")

if [ -z "$DEPLOY_URL" ]; then
    echo "⚠️  No deployment URL found - service may not be deployed yet"
    echo "Check Railway dashboard: railway open"
else
    echo "URL: https://$DEPLOY_URL"
    
    # Check health endpoint
    echo -e "\n❤️  Checking health endpoint..."
    HEALTH_URL="https://$DEPLOY_URL/api/health"
    
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "FAILED")
    
    if [[ "$response" == "FAILED" ]]; then
        echo "❌ Failed to connect to health endpoint"
    else
        http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
        body=$(echo "$response" | grep -v "HTTP_CODE:")
        
        if [ "$http_code" == "200" ]; then
            echo "✅ Health check passed!"
            echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
        else
            echo "❌ Health check failed (HTTP $http_code)"
            echo "$body"
        fi
    fi
    
    # Check detailed health
    echo -e "\n📊 Checking detailed health..."
    DETAILED_URL="https://$DEPLOY_URL/api/health/detailed"
    
    detailed_response=$(curl -s "$DETAILED_URL" 2>/dev/null || echo "{}")
    if [ "$detailed_response" != "{}" ]; then
        echo "$detailed_response" | python3 -m json.tool 2>/dev/null || echo "$detailed_response"
    fi
fi

# Show recent logs
echo -e "\n📜 Recent deployment logs (last 10 lines):"
railway logs --tail 10 2>/dev/null || echo "Could not fetch logs"

echo -e "\n✅ Status check complete!"
echo "For live logs: railway logs"
echo "For dashboard: railway open"