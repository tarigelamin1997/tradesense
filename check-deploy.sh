#!/bin/bash

echo "🔍 Checking Railway Deployment"
echo "============================="

# Get the build URL from the last deployment
BUILD_URL="https://railway.com/project/08df85d3-c89a-4082-887b-8361569a01f3/service/7be4cb72-a5da-4f3c-aec2-909357c08518"

echo "Build logs: $BUILD_URL"
echo ""

# Check health endpoint
echo "Checking health endpoint..."
for i in {1..30}; do
    response=$(curl -s -o /dev/null -w "%{http_code}" https://tradesense-production.up.railway.app/health)
    if [ "$response" = "200" ]; then
        echo "✅ Backend is UP! (HTTP $response)"
        curl -s https://tradesense-production.up.railway.app/health | jq .
        break
    else
        echo "⏳ Waiting... (attempt $i/30, status: $response)"
        sleep 10
    fi
done

echo ""
echo "Testing API endpoints:"
echo "- Health: https://tradesense-production.up.railway.app/health"
echo "- API: https://tradesense-production.up.railway.app/api"
echo "- Docs: https://tradesense-production.up.railway.app/docs"