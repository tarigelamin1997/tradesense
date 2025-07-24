#!/bin/bash

# Force Gateway Deployment Script
# This ensures the gateway is deployed with the latest code

set -e

echo "🚀 Force Gateway Deployment"
echo "=========================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}Railway CLI not found. Please install it first:${NC}"
    echo "npm install -g @railway/cli"
    exit 1
fi

# Check if we're in the project root
if [ ! -d "services/gateway" ]; then
    echo -e "${RED}This script must be run from the project root directory${NC}"
    exit 1
fi

echo -e "${BLUE}Step 1: Preparing gateway service${NC}"
cd services/gateway

# Create a version file to force rebuild
echo "DEPLOYMENT_VERSION=$(date +%Y%m%d_%H%M%S)" > .deployment_version
echo "FORCE_REBUILD=true" >> .deployment_version

echo -e "${BLUE}Step 2: Building Docker image locally${NC}"
docker build -t tradesense-gateway:latest . --no-cache

echo -e "${BLUE}Step 3: Deploying to Railway${NC}"
echo "Please ensure RAILWAY_TOKEN is set in your environment"

# Deploy with explicit service name
railway up --service tradesense-gateway

echo -e "${BLUE}Step 4: Waiting for deployment to stabilize${NC}"
sleep 30

echo -e "${BLUE}Step 5: Verifying deployment${NC}"

# Test the auth endpoint
echo -n "Testing /auth/token endpoint: "
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://tradesense-gateway-production.up.railway.app/auth/token -H "Content-Type: application/x-www-form-urlencoded" -d "username=test&password=test")

if [ "$response" = "401" ] || [ "$response" = "422" ]; then
    echo -e "${GREEN}✅ Success! (HTTP $response)${NC}"
    echo -e "${GREEN}Gateway is now properly routing auth requests${NC}"
elif [ "$response" = "404" ]; then
    echo -e "${RED}❌ Failed! Still returning 404${NC}"
    echo -e "${YELLOW}The deployment may need manual intervention in Railway dashboard${NC}"
    exit 1
else
    echo -e "${YELLOW}⚠️  Unexpected response: HTTP $response${NC}"
fi

# Test other routes
echo ""
echo -e "${BLUE}Testing other routes:${NC}"

# Test health endpoint
echo -n "Health endpoint: "
health_response=$(curl -s -o /dev/null -w "%{http_code}" https://tradesense-gateway-production.up.railway.app/health)
if [ "$health_response" = "200" ]; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${RED}❌ Unhealthy (HTTP $health_response)${NC}"
fi

# Test services endpoint
echo -n "Services endpoint: "
services_response=$(curl -s -o /dev/null -w "%{http_code}" https://tradesense-gateway-production.up.railway.app/services)
if [ "$services_response" = "200" ]; then
    echo -e "${GREEN}✅ Available${NC}"
else
    echo -e "${RED}❌ Unavailable (HTTP $services_response)${NC}"
fi

echo ""
echo -e "${BLUE}Deployment Summary:${NC}"
echo "===================="

if [ "$response" = "401" ] || [ "$response" = "422" ]; then
    echo -e "${GREEN}✅ Gateway deployment successful!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Update frontend environment variables:"
    echo "   VITE_API_BASE_URL=https://tradesense-gateway-production.up.railway.app"
    echo "   VITE_API_URL=https://tradesense-gateway-production.up.railway.app"
    echo ""
    echo "2. Redeploy frontend on Vercel"
    echo ""
    echo "3. Test authentication through the gateway"
else
    echo -e "${RED}❌ Gateway deployment failed${NC}"
    echo ""
    echo "Manual steps required:"
    echo "1. Log into Railway dashboard"
    echo "2. Navigate to gateway service"
    echo "3. Click 'Redeploy' with 'Clear build cache' option"
    echo "4. Monitor deployment logs"
    echo "5. Run this script again to verify"
fi

# Cleanup
cd ../..
rm -f services/gateway/.deployment_version