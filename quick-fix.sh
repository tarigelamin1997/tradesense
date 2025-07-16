#!/bin/bash

echo "🚑 TradeSense Emergency Docker Fix"
echo "=================================="

# Stop everything first
echo "🛑 Stopping all containers..."
docker compose -f docker-compose.simple-alt.yml down 2>/dev/null || true
docker compose -f docker-compose.fixed.yml down 2>/dev/null || true

# Start with the fixed configuration
echo "🚀 Starting with corrected port mappings..."
docker compose -f docker-compose.fixed.yml up -d

# Wait a moment
echo "⏳ Waiting for services to initialize..."
sleep 15

# Check what's actually running
echo ""
echo "📊 Service Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Verify frontend is accessible
echo ""
echo "🔍 Checking frontend..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 | grep -q "200\|304"; then
    echo "✅ Frontend is responding!"
else
    echo "⚠️  Frontend might still be starting up. Checking logs..."
    docker compose -f docker-compose.fixed.yml logs --tail=20 frontend
fi

echo ""
echo "=================================="
echo "🎯 ACCESS YOUR APP HERE:"
echo "   Frontend: http://localhost:3001"  
echo "   Backend: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Login with:"
echo "   Email: test@example.com"
echo "   Password: testpass123"
echo ""
echo "🐛 Debug commands:"
echo "   docker compose -f docker-compose.fixed.yml logs -f frontend"
echo "   docker compose -f docker-compose.fixed.yml logs -f backend"
echo "=================================="