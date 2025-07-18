#!/bin/bash

echo "🔧 Railway Quick Fix & Deploy"
echo "============================"

# Function to test endpoint
test_endpoint() {
    local url=$1
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    echo "$response"
}

# Menu
echo "Choose an option:"
echo "1) Deploy with simple Dockerfile (fastest)"
echo "2) Deploy with full Dockerfile"
echo "3) Check deployment status"
echo "4) View recent logs"
echo "5) Restart service"
echo "6) Update environment variables"

read -p "Option (1-6): " choice

case $choice in
    1)
        echo "Deploying with simple Dockerfile..."
        # Update railway.toml
        sed -i 's/dockerfilePath = .*/dockerfilePath = "Dockerfile.railway"/' railway.toml
        git add railway.toml
        git commit -m "fix: Use simple Dockerfile" --no-verify
        git push
        railway up
        ;;
    2)
        echo "Deploying with full Dockerfile..."
        sed -i 's/dockerfilePath = .*/dockerfilePath = "src\/backend\/Dockerfile"/' railway.toml
        git add railway.toml
        git commit -m "fix: Use full Dockerfile" --no-verify
        git push
        railway up
        ;;
    3)
        echo "Checking deployment status..."
        echo -n "Health check: "
        status=$(test_endpoint "https://tradesense-production.up.railway.app/health")
        if [ "$status" = "200" ]; then
            echo "✅ OK ($status)"
            curl -s https://tradesense-production.up.railway.app/health | jq .
        else
            echo "❌ Failed ($status)"
        fi
        ;;
    4)
        echo "Recent logs:"
        railway logs | tail -50
        ;;
    5)
        echo "Restarting service..."
        railway restart
        ;;
    6)
        echo "Current environment variables:"
        railway variables
        echo ""
        echo "Add variable: railway variables set KEY=VALUE"
        ;;
esac