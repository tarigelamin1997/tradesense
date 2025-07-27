#!/bin/bash
# Simplified Railway deployment script
set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 TradeSense Railway Deployment${NC}"
echo "=================================="
echo ""

# Services to deploy
SERVICES=("gateway" "auth" "trading" "analytics" "billing" "market-data" "ai")

# Create deployment directory
mkdir -p deployments
DEPLOY_ID="deploy_$(date +%Y%m%d_%H%M%S)"
mkdir -p "deployments/$DEPLOY_ID"

# Function to deploy a service
deploy_service() {
    local service=$1
    echo -e "${BLUE}Deploying ${service}...${NC}"
    
    cd "services/${service}"
    
    # Copy shared backend code
    cp -r ../../src/backend ./backend
    
    # Deploy to Railway
    railway up --detach --service "$service" || {
        echo -e "${RED}❌ Failed to deploy ${service}${NC}"
        cd - > /dev/null
        return 1
    }
    
    # Clean up
    rm -rf ./backend
    cd - > /dev/null
    
    echo -e "${GREEN}✅ ${service} deployed${NC}"
    return 0
}

# Deploy all services
FAILED_SERVICES=()
for service in "${SERVICES[@]}"; do
    if deploy_service "$service"; then
        echo "$service: SUCCESS" >> "deployments/$DEPLOY_ID/status.txt"
    else
        echo "$service: FAILED" >> "deployments/$DEPLOY_ID/status.txt"
        FAILED_SERVICES+=("$service")
    fi
    echo ""
done

# Summary
echo "======================================"
if [ ${#FAILED_SERVICES[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ All services deployed successfully!${NC}"
else
    echo -e "${RED}❌ Some services failed to deploy:${NC}"
    printf '%s\n' "${FAILED_SERVICES[@]}"
fi
echo ""
echo "Deployment ID: $DEPLOY_ID"
echo ""

# Set environment variables after deployment
echo -e "${BLUE}Setting environment variables...${NC}"
for service in "${SERVICES[@]}"; do
    echo "Configuring $service..."
    
    # Set basic security vars
    railway variables --set "ENABLE_SECURITY_HEADERS=true" \
                     --set "ENABLE_RATE_LIMITING=true" \
                     --set "ENABLE_AUDIT_LOGGING=true" \
                     --service "$service" || echo "  Failed to set vars for $service"
done

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Check service health: ./scripts/monitor-railway-health.sh"
echo "2. View logs: railway logs --service <service-name>"
echo "3. Set up secrets manually in Railway dashboard"