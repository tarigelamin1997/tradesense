#!/bin/bash

echo "🚀 TradeSense Hybrid Mode (Docker DBs + Local App)"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Function to check if port is in use
check_port() {
    lsof -i :$1 >/dev/null 2>&1
}

# Step 1: Start only database services in Docker
echo -e "${YELLOW}📦 Starting database services in Docker...${NC}"
cat > docker-compose.db-only.yml << 'EOF'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: tradesense
      POSTGRES_PASSWORD: tradesense123
      POSTGRES_DB: tradesense
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tradesense"]
      interval: 2s
      retries: 10

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --requirepass tradesense123
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
EOF

# Stop any existing database containers
docker compose -f docker-compose.db-only.yml down 2>/dev/null

# Start fresh
docker compose -f docker-compose.db-only.yml up -d

# Wait for databases
echo -e "${YELLOW}⏳ Waiting for databases to be ready...${NC}"
sleep 5

# Check if databases are running
if docker compose -f docker-compose.db-only.yml ps | grep -q "postgres.*healthy"; then
    echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
else
    echo -e "${RED}❌ PostgreSQL failed to start${NC}"
    exit 1
fi

if docker compose -f docker-compose.db-only.yml ps | grep -q "redis.*Up"; then
    echo -e "${GREEN}✅ Redis is ready${NC}"
else
    echo -e "${RED}❌ Redis failed to start${NC}"
    exit 1
fi

# Step 2: Start Backend Locally
echo -e "\n${YELLOW}🔧 Starting Backend locally...${NC}"
cd src/backend

# Create .env file for backend
cat > .env << 'EOF'
DATABASE_URL=postgresql://tradesense:tradesense123@localhost:5432/tradesense
REDIS_URL=redis://:tradesense123@localhost:6379/0
SECRET_KEY=local-dev-secret-key
JWT_SECRET_KEY=local-dev-jwt-secret
APP_ENV=development
DEBUG=true
EOF

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate
echo "Installing backend dependencies..."
pip install -q -r ../../requirements.txt 2>/dev/null
pip install -q email-validator jinja2 aiohttp redis 2>/dev/null

# Start backend in background
echo -e "${YELLOW}Starting backend server...${NC}"
python main.py > ../../backend.log 2>&1 &
BACKEND_PID=$!
cd ../..

# Wait for backend to start
sleep 5
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}❌ Backend failed to start. Check backend.log${NC}"
    tail -20 backend.log
    exit 1
fi

# Step 3: Start Frontend Locally
echo -e "\n${YELLOW}🎨 Starting Frontend locally...${NC}"
cd frontend

# Ensure node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Create .env for frontend
cat > .env.local << 'EOF'
VITE_API_BASE_URL=http://localhost:8000
PUBLIC_API_URL=http://localhost:8000
EOF

# Start frontend
echo -e "${YELLOW}Starting frontend server...${NC}"
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend
echo -e "${YELLOW}⏳ Waiting for frontend to start...${NC}"
sleep 10

# Final status
echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}✅ TradeSense is running in Hybrid Mode!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""
echo "📍 Access points:"
echo "   Frontend: http://localhost:3001"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🗄️ Databases (in Docker):"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo ""
echo "📝 Test credentials:"
echo "   Email: test@example.com"
echo "   Password: testpass123"
echo ""
echo "🛑 To stop everything:"
echo "   Press Ctrl+C, then run:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   docker compose -f docker-compose.db-only.yml down"
echo ""
echo "📋 Logs:"
echo "   Backend: tail -f backend.log"
echo "   Frontend: See terminal output above"
echo -e "${GREEN}==================================================${NC}"

# Keep script running
wait