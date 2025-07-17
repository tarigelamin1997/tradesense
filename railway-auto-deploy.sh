#!/bin/bash

# Railway Automated Deployment & Monitoring Script
# This script handles the entire deployment process automatically

set -e  # Exit on error

echo "🚀 TradeSense Railway Automated Deployment"
echo "========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check deployment status
check_deployment_health() {
    local max_attempts=30
    local attempt=1
    local health_url="$1/api/health"
    
    echo -e "\n${YELLOW}🔍 Checking deployment health...${NC}"
    echo "URL: $health_url"
    
    while [ $attempt -le $max_attempts ]; do
        echo -ne "\rAttempt $attempt/$max_attempts..."
        
        # Try to hit the health endpoint
        response=$(curl -s -o /dev/null -w "%{http_code}" "$health_url" 2>/dev/null || echo "000")
        
        if [ "$response" = "200" ]; then
            echo -e "\n${GREEN}✅ Backend is healthy!${NC}"
            curl -s "$health_url" | python3 -m json.tool
            return 0
        elif [ "$response" = "502" ] || [ "$response" = "503" ]; then
            echo -ne " (Service starting...)"
        elif [ "$response" = "000" ]; then
            echo -ne " (Connection failed...)"
        else
            echo -ne " (HTTP $response)"
        fi
        
        sleep 10
        ((attempt++))
    done
    
    echo -e "\n${RED}❌ Health check failed after $max_attempts attempts${NC}"
    return 1
}

# Step 1: Verify Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not installed${NC}"
    echo "Install with: curl -fsSL https://railway.app/install.sh | sh"
    exit 1
fi

# Step 2: Check if logged in
railway whoami &>/dev/null || {
    echo -e "${YELLOW}Please login to Railway:${NC}"
    railway login
}

# Step 3: Ensure we're linked to a project
railway status &>/dev/null || {
    echo -e "${YELLOW}Linking to Railway project...${NC}"
    railway link
}

# Step 4: Display current status
echo -e "\n${BLUE}📊 Current Configuration:${NC}"
railway status

# Step 5: Set environment variables
echo -e "\n${YELLOW}📝 Configuring environment variables...${NC}"
railway variables --set "JWT_SECRET_KEY=REDACTED" \
    --set "SECRET_KEY=REDACTED" \
    --set "CORS_ORIGINS_STR=http://localhost:3000" \
    --set "ADMIN_EMAIL=support@tradesense.ai" \
    --set "ENVIRONMENT=production" \
    --set "PORT=8000" &>/dev/null

echo -e "${GREEN}✅ Environment variables configured${NC}"

# Step 6: Deploy
echo -e "\n${YELLOW}🚂 Deploying to Railway...${NC}"
DEPLOY_OUTPUT=$(railway up 2>&1)
echo "$DEPLOY_OUTPUT"

# Extract deployment URL
BUILD_URL=$(echo "$DEPLOY_OUTPUT" | grep -o 'https://railway.com/project/[^&]*' | head -1 || echo "")

if [ -z "$BUILD_URL" ]; then
    echo -e "${RED}❌ Failed to get deployment URL${NC}"
else
    echo -e "\n${BLUE}🔗 Build logs: ${BUILD_URL}${NC}"
fi

# Step 7: Get or create domain
echo -e "\n${YELLOW}🌐 Checking domain...${NC}"
DOMAIN=$(railway domain 2>&1 | grep -o 'https://[^ ]*' || echo "")

if [ -z "$DOMAIN" ]; then
    echo "No domain found, generating..."
    DOMAIN=$(railway domain | grep -o 'https://[^ ]*')
fi

echo -e "${GREEN}✅ Domain: $DOMAIN${NC}"

# Step 8: Wait for deployment and check health
if [ ! -z "$DOMAIN" ]; then
    check_deployment_health "$DOMAIN"
fi

# Step 9: Final summary
echo -e "\n${BLUE}📋 Deployment Summary:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Backend URL: ${GREEN}${DOMAIN}${NC}"
echo -e "Health Check: ${GREEN}${DOMAIN}/api/health${NC}"
echo -e "API Docs: ${GREEN}${DOMAIN}/api/docs${NC}"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Update frontend/.env.production with:"
echo "   VITE_API_BASE_URL=$DOMAIN"
echo ""
echo "2. Update CORS in Railway:"
echo "   railway variables --set \"CORS_ORIGINS_STR=http://localhost:3000,YOUR_VERCEL_URL\""
echo ""
echo "3. Monitor logs:"
echo "   railway logs"
echo ""
echo -e "${GREEN}✅ Deployment automation complete!${NC}"