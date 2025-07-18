#!/bin/bash

echo "🔍 Railway Deployment Status Checker"
echo "==================================="

# Get the deployment URL from the last deployment
DEPLOYMENT_URL=$(railway up 2>&1 | grep -o 'https://railway.com/project/[^&]*' | head -1)

if [ -z "$DEPLOYMENT_URL" ]; then
    echo "❌ No active deployment found"
    echo "Run 'railway up' to start a new deployment"
    exit 1
fi

echo "📊 Deployment URL: $DEPLOYMENT_URL"
echo ""
echo "🚂 Current Status:"
railway status

echo ""
echo "📝 Recent Activity:"
echo "To view logs, run: railway logs"
echo "To open dashboard, run: railway open"

# Check if the service has a domain
echo ""
echo "🌐 Service Domain:"
railway domain 2>/dev/null || echo "No domain set yet. Run 'railway domain' to generate one."