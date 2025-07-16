#!/bin/bash

echo "🔄 Restarting frontend container..."

# Restart just the frontend service
docker compose -f docker-compose.fixed.yml restart frontend

echo "⏳ Waiting for frontend to be ready..."
sleep 10

echo "✅ Frontend restarted. Please refresh your browser."
echo ""
echo "🔍 To check logs:"
echo "   docker compose -f docker-compose.fixed.yml logs -f frontend"