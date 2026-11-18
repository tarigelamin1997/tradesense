#!/bin/bash

# Quick Docker setup for TradeSense
echo "🚀 TradeSense Docker Quick Start"
echo "================================"

# Create a simple docker-compose file
cat > docker-compose.simple.yml << 'EOF'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: tradesense
      POSTGRES_PASSWORD: tradesense123
      POSTGRES_DB: tradesense
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tradesense"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --requirepass tradesense123

  backend:
    image: python:3.11-slim
    working_dir: /app
    volumes:
      - ./src/backend:/app
      - ./requirements.txt:/app/requirements.txt
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://tradesense:tradesense123@postgres:5432/tradesense
      REDIS_URL: redis://:tradesense123@redis:6379/0
      SECRET_KEY: test-secret-key
      JWT_SECRET_KEY: test-jwt-secret
    command: |
      bash -c "
        pip install -r requirements.txt &&
        pip install email-validator jinja2 aiohttp &&
        python main.py
      "
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

  frontend:
    image: node:18-alpine
    working_dir: /app
    volumes:
      - ./frontend:/app
    ports:
      - "5173:5173"
    environment:
      VITE_API_BASE_URL: http://localhost:8000
    command: |
      sh -c "
        npm install &&
        npm run dev -- --host 0.0.0.0
      "
    depends_on:
      - backend
EOF

echo "📦 Starting services with Docker Compose..."
echo ""

# Run with sudo if needed
if ! docker ps >/dev/null 2>&1; then
    echo "🔐 Docker requires sudo. Running with sudo..."
    sudo docker compose -f docker-compose.simple.yml up
else
    docker compose -f docker-compose.simple.yml up
fi