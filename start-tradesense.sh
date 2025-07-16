#!/bin/bash

echo "🚀 Starting TradeSense with Docker"
echo "=================================="

# Function to check if we need sudo
needs_sudo() {
    if ! docker ps >/dev/null 2>&1; then
        echo "true"
    else
        echo "false"
    fi
}

# Set docker command
if [ "$(needs_sudo)" = "true" ]; then
    DOCKER_CMD="sudo docker"
    echo "🔐 Running with sudo..."
else
    DOCKER_CMD="docker"
fi

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
$DOCKER_CMD compose -f docker-compose.simple.yml down 2>/dev/null || true
$DOCKER_CMD compose -f docker-compose.simple-alt.yml down 2>/dev/null || true

# Kill any processes using our ports
echo "🔍 Checking for port conflicts..."
for port in 5432 5433 6379 6380 8000 5173; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo "⚠️  Port $port is in use, trying to free it..."
        fuser -k $port/tcp 2>/dev/null || true
    fi
done

# Start with the alternative config (different ports)
echo ""
echo "📦 Starting services..."
$DOCKER_CMD compose -f docker-compose.simple-alt.yml up -d

# Wait for services to start
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "📊 Checking service status..."
$DOCKER_CMD ps

# Show access information
echo ""
echo "=================================="
echo "✅ TradeSense should be running!"
echo "=================================="
echo ""
echo "📍 Access points:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🗄️ Database is on port 5433 (not 5432)"
echo "📦 Redis is on port 6380 (not 6379)"
echo ""
echo "📝 Test credentials:"
echo "   Email: test@example.com"
echo "   Password: testpass123"
echo ""
echo "📋 View logs:"
echo "   All: $DOCKER_CMD compose -f docker-compose.simple-alt.yml logs -f"
echo "   Backend: $DOCKER_CMD compose -f docker-compose.simple-alt.yml logs -f backend"
echo "   Frontend: $DOCKER_CMD compose -f docker-compose.simple-alt.yml logs -f frontend"
echo ""
echo "🛑 To stop:"
echo "   $DOCKER_CMD compose -f docker-compose.simple-alt.yml down"
echo "=================================="