#!/bin/bash

echo "🚀 Quick Railway Status Check"
echo "============================"

# Check health endpoint
echo -n "Backend Status: "
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" https://tradesense-production.up.railway.app/api/health 2>/dev/null)
http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
body=$(echo "$response" | grep -v "HTTP_CODE:")

if [ "$http_code" = "200" ]; then
    echo "✅ ONLINE!"
    echo "Response: $body"
    echo ""
    echo "🎉 Your backend is ready!"
    echo "📚 API Docs: https://tradesense-production.up.railway.app/api/docs"
elif [ "$http_code" = "502" ]; then
    echo "⏳ Starting up (502 Bad Gateway)"
    echo "The app might be building or there's another startup error."
    echo "Check Railway dashboard for logs."
else
    echo "❌ Error (HTTP $http_code)"
    echo "Response: $body"
fi

echo ""
echo "To check deployment logs:"
echo "1. Visit: https://railway.app/project/08df85d3-c89a-4082-887b-8361569a01f3"
echo "2. Or run: railway open"