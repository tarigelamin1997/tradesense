#!/bin/bash

echo "🚀 TradeSense Microservices Deployment"
echo "====================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to deploy a service
deploy_service() {
    local service_name=$1
    local service_path=$2
    
    echo -e "\n${YELLOW}Deploying $service_name...${NC}"
    
    cd $service_path
    
    # Initialize git if needed
    if [ ! -d .git ]; then
        git init
        git add .
        git commit -m "Initial commit for $service_name"
    fi
    
    # Link to Railway
    echo "Linking to Railway..."
    railway link
    
    # Deploy
    echo "Deploying to Railway..."
    railway up
    
    echo -e "${GREEN}✓ $service_name deployed${NC}"
    cd - > /dev/null
}

# Main menu
echo "Select deployment option:"
echo "1) Deploy Gateway only"
echo "2) Deploy Auth Service only"
echo "3) Deploy Trading Service only"
echo "4) Deploy Core Services (Gateway + Auth + Trading)"
echo "5) Deploy All Services"
echo "6) Check Service Status"

read -p "Option (1-6): " choice

case $choice in
    1)
        deploy_service "Gateway" "services/gateway"
        ;;
    2)
        deploy_service "Auth" "services/auth"
        ;;
    3)
        deploy_service "Trading" "services/trading"
        ;;
    4)
        echo "Deploying core services..."
        deploy_service "Gateway" "services/gateway"
        deploy_service "Auth" "services/auth"
        deploy_service "Trading" "services/trading"
        ;;
    5)
        echo "Deploying all services..."
        for service in gateway auth trading analytics market-data billing ai; do
            if [ -d "services/$service" ]; then
                deploy_service "$service" "services/$service"
            fi
        done
        ;;
    6)
        echo -e "\n${YELLOW}Checking service status...${NC}"
        echo "Gateway: $(curl -s https://tradesense-gateway.up.railway.app/health | jq -r .status 2>/dev/null || echo 'Not deployed')"
        echo "Auth: $(curl -s https://tradesense-auth.up.railway.app/health | jq -r .status 2>/dev/null || echo 'Not deployed')"
        echo "Trading: $(curl -s https://tradesense-trading.up.railway.app/health | jq -r .status 2>/dev/null || echo 'Not deployed')"
        ;;
esac

echo -e "\n${GREEN}Deployment complete!${NC}"