#!/bin/bash

echo "🧹 Cleaning up build artifacts..."

# Stop containers
docker compose -f docker-compose.fixed.yml down

# Remove the .svelte-kit directory which contains stale build artifacts
rm -rf frontend/.svelte-kit
rm -rf frontend/node_modules/.vite

echo "🏗️ Starting with fresh build..."

# Use a modified docker-compose that ensures fresh build
cat > docker-compose.rebuild.yml << 'EOF'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: tradesense
      POSTGRES_PASSWORD: tradesense123
      POSTGRES_DB: tradesense
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tradesense"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"
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
      - "3001:3001"
    environment:
      VITE_API_BASE_URL: http://localhost:8000
      NODE_ENV: development
    command: |
      sh -c "
        echo 'Cleaning old build artifacts...' &&
        rm -rf .svelte-kit node_modules/.vite &&
        echo 'Installing dependencies...' &&
        npm install &&
        echo 'Building SvelteKit...' &&
        npm run build &&
        echo 'Starting dev server...' &&
        npm run dev -- --host 0.0.0.0
      "
    depends_on:
      - backend
EOF

echo "🚀 Starting services with fresh build..."
docker compose -f docker-compose.rebuild.yml up -d

echo "⏳ Waiting for frontend to build (this may take a minute)..."
sleep 30

echo "✅ Rebuild complete!"
echo ""
echo "🌐 Try accessing: http://localhost:3001/register"
echo ""
echo "📋 To monitor the build progress:"
echo "   docker compose -f docker-compose.rebuild.yml logs -f frontend"