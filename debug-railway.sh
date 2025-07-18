#!/bin/bash

echo "🔍 Railway Backend Debug & Deploy Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Check Railway CLI
echo -e "\n${YELLOW}1. Checking Railway CLI...${NC}"
if command_exists railway; then
    echo -e "${GREEN}✓ Railway CLI installed${NC}"
    railway version
else
    echo -e "${RED}✗ Railway CLI not found${NC}"
    echo "Install with: npm install -g @railway/cli"
    exit 1
fi

# 2. Check Railway login status
echo -e "\n${YELLOW}2. Checking Railway login...${NC}"
if railway whoami >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Logged in as: $(railway whoami)${NC}"
else
    echo -e "${RED}✗ Not logged in to Railway${NC}"
    echo "Run: railway login"
    exit 1
fi

# 3. Test Docker build locally
echo -e "\n${YELLOW}3. Testing Docker build locally...${NC}"
cd /home/tarigelamin/Desktop/tradesense

# Build with proper context
echo "Building Docker image..."
if docker build -f src/backend/Dockerfile -t tradesense-test . > /tmp/docker-build.log 2>&1; then
    echo -e "${GREEN}✓ Docker build successful${NC}"
else
    echo -e "${RED}✗ Docker build failed${NC}"
    echo "Last 20 lines of build log:"
    tail -20 /tmp/docker-build.log
    exit 1
fi

# 4. Test run locally
echo -e "\n${YELLOW}4. Testing Docker run locally...${NC}"
echo "Starting container..."
docker run -d --name tradesense-test-run \
    -p 8000:8000 \
    -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/tradesense" \
    -e JWT_SECRET_KEY="test-secret-key" \
    -e ENVIRONMENT="development" \
    -e PORT=8000 \
    tradesense-test > /tmp/docker-run.log 2>&1

# Wait for startup
echo "Waiting for container to start..."
sleep 5

# Check if container is running
if docker ps | grep -q tradesense-test-run; then
    echo -e "${GREEN}✓ Container is running${NC}"
    
    # Test health endpoint
    echo "Testing health endpoint..."
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo -e "${GREEN}✓ Health check passed${NC}"
    else
        echo -e "${RED}✗ Health check failed${NC}"
        echo "Container logs:"
        docker logs tradesense-test-run | tail -20
    fi
else
    echo -e "${RED}✗ Container failed to start${NC}"
    echo "Container logs:"
    docker logs tradesense-test-run 2>&1 | tail -20
fi

# Cleanup
docker stop tradesense-test-run >/dev/null 2>&1
docker rm tradesense-test-run >/dev/null 2>&1

# 5. Check Railway project
echo -e "\n${YELLOW}5. Checking Railway project...${NC}"
if railway status >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Railway project linked${NC}"
    railway status
else
    echo -e "${RED}✗ No Railway project linked${NC}"
    echo "Run: railway link"
    exit 1
fi

# 6. Deploy to Railway
echo -e "\n${YELLOW}6. Ready to deploy?${NC}"
echo "Current git branch: $(git branch --show-current)"
echo "Last commit: $(git log -1 --oneline)"
read -p "Deploy to Railway? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${YELLOW}Deploying to Railway...${NC}"
    railway up
else
    echo "Deployment cancelled"
fi