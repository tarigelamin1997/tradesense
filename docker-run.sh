#!/bin/bash

# Simple Docker run script for TradeSense
echo "🚀 Starting TradeSense with Docker"
echo "=================================="

# Stop any existing containers
echo "🧹 Cleaning up..."
sudo docker stop tradesense-db tradesense-redis tradesense-backend tradesense-frontend 2>/dev/null
sudo docker rm tradesense-db tradesense-redis tradesense-backend tradesense-frontend 2>/dev/null

# Start PostgreSQL
echo ""
echo "🗄️ Starting PostgreSQL..."
sudo docker run -d --name tradesense-db \
  -e POSTGRES_USER=tradesense \
  -e POSTGRES_PASSWORD=tradesense123 \
  -e POSTGRES_DB=tradesense \
  -p 5432:5432 \
  postgres:15-alpine

# Start Redis
echo "📦 Starting Redis..."
sudo docker run -d --name tradesense-redis \
  -p 6379:6379 \
  redis:7-alpine

# Wait for databases
echo "⏳ Waiting for databases to start..."
sleep 10

# Build and run backend
echo ""
echo "🔧 Building Backend..."
cd src/backend
sudo docker build -t tradesense-backend . || {
    echo "❌ Backend build failed. Creating simple Dockerfile..."
    cat > Dockerfile.simple << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt || pip install fastapi uvicorn sqlalchemy psycopg2-binary
COPY . .
CMD ["python", "main.py"]
EOF
    sudo docker build -f Dockerfile.simple -t tradesense-backend .
}

echo "🚀 Starting Backend..."
sudo docker run -d --name tradesense-backend \
  -p 8000:8000 \
  --link tradesense-db:postgres \
  --link tradesense-redis:redis \
  -e DATABASE_URL="postgresql://tradesense:tradesense123@postgres:5432/tradesense" \
  -e REDIS_URL="redis://redis:6379/0" \
  -e SECRET_KEY="test-secret-key" \
  -e JWT_SECRET_KEY="test-jwt-secret" \
  tradesense-backend

cd ../..

# Build and run frontend
echo ""
echo "🎨 Building Frontend..."
cd frontend
sudo docker build -t tradesense-frontend . || {
    echo "❌ Frontend build failed. Creating simple Dockerfile..."
    cat > Dockerfile.simple << 'EOF'
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
EOF
    sudo docker build -f Dockerfile.simple -t tradesense-frontend .
}

echo "🚀 Starting Frontend..."
sudo docker run -d --name tradesense-frontend \
  -p 5173:5173 \
  -e VITE_API_BASE_URL="http://localhost:8000" \
  tradesense-frontend

cd ..

# Show status
echo ""
echo "=================================="
echo "✅ TradeSense is starting up!"
echo "=================================="
echo ""
echo "📍 Checking services..."
sleep 5

# Check if services are running
if sudo docker ps | grep -q tradesense-backend; then
    echo "✅ Backend is running"
else
    echo "❌ Backend failed to start"
    echo "Check logs: sudo docker logs tradesense-backend"
fi

if sudo docker ps | grep -q tradesense-frontend; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend failed to start"
    echo "Check logs: sudo docker logs tradesense-frontend"
fi

echo ""
echo "📍 Access points:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Test credentials:"
echo "   Email: test@example.com"
echo "   Password: testpass123"
echo ""
echo "🛑 To stop: sudo docker stop tradesense-db tradesense-redis tradesense-backend tradesense-frontend"
echo "📋 View logs: sudo docker logs <container-name>"
echo "=================================="