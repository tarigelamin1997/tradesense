#!/bin/bash

echo "🔄 Monitoring Railway Deployment"
echo "================================"

URL="https://tradesense-production.up.railway.app/api/health"
CHECK_INTERVAL=10
MAX_CHECKS=60  # 10 minutes max

echo "Checking: $URL"
echo "Will check every ${CHECK_INTERVAL}s for up to ${MAX_CHECKS} attempts"
echo ""

attempt=1
while [ $attempt -le $MAX_CHECKS ]; do
    echo -n "[$attempt/$MAX_CHECKS] $(date +%H:%M:%S) - "
    
    response=$(curl -s -w "\n%{http_code}" "$URL" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo "✅ SUCCESS! Backend is online!"
        echo "Response:"
        echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
        echo ""
        echo "🎉 Your backend is ready at: https://tradesense-production.up.railway.app"
        echo "📚 API Docs: https://tradesense-production.up.railway.app/api/docs"
        exit 0
    elif [ "$http_code" = "502" ]; then
        echo "⏳ Application starting up..."
    elif [ "$http_code" = "000" ]; then
        echo "❌ Connection failed"
    else
        echo "⚠️  HTTP $http_code"
        if [ ! -z "$body" ]; then
            echo "   Response: $body"
        fi
    fi
    
    if [ $attempt -lt $MAX_CHECKS ]; then
        sleep $CHECK_INTERVAL
    fi
    
    ((attempt++))
done

echo ""
echo "❌ Deployment monitoring timed out after $((MAX_CHECKS * CHECK_INTERVAL / 60)) minutes"
echo ""
echo "Please check Railway dashboard for deployment logs:"
echo "https://railway.app/dashboard"