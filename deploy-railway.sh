#!/bin/bash

echo "🚀 Automated Railway Deployment Script"
echo "====================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not found. Please install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Railway CLI found${NC}"

# Check if we're in the right directory
if [ ! -f "railway.json" ]; then
    echo -e "${RED}❌ railway.json not found. Are you in the project root?${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Project directory verified${NC}"

# Set environment variables
echo -e "\n${YELLOW}📝 Setting environment variables...${NC}"
railway variables --set "JWT_SECRET_KEY=REDACTED" \
    --set "SECRET_KEY=REDACTED" \
    --set "CORS_ORIGINS_STR=http://localhost:3000" \
    --set "ADMIN_EMAIL=support@tradesense.ai" \
    --set "ENVIRONMENT=production" \
    --set "PORT=8000"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Environment variables set successfully${NC}"
else
    echo -e "${RED}❌ Failed to set environment variables${NC}"
    exit 1
fi

# Deploy to Railway
echo -e "\n${YELLOW}🚂 Deploying to Railway...${NC}"
railway up

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment initiated successfully${NC}"
    echo -e "\n${YELLOW}📊 Deployment status:${NC}"
    railway status
    
    echo -e "\n${YELLOW}💡 Next steps:${NC}"
    echo "1. Monitor deployment at: https://railway.app/dashboard"
    echo "2. Once deployed, get your domain with: railway domain"
    echo "3. Check logs with: railway logs"
else
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

echo -e "\n${GREEN}✅ Script completed!${NC}"