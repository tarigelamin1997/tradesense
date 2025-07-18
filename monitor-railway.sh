#!/bin/bash

echo "📊 Railway Real-time Monitor"
echo "==========================="
echo "Press Ctrl+C to stop"
echo ""

# Function to check health
check_health() {
    response=$(curl -s -o /dev/null -w "%{http_code}" https://tradesense-production.up.railway.app/health)
    if [ "$response" = "200" ]; then
        echo -e "\033[0;32m✓ Health: OK (200)\033[0m"
    else
        echo -e "\033[0;31m✗ Health: Failed ($response)\033[0m"
    fi
}

# Monitor loop
while true; do
    clear
    echo "📊 Railway Real-time Monitor"
    echo "==========================="
    echo "Time: $(date)"
    echo ""
    
    # Check deployment status
    echo "🚂 Railway Status:"
    railway status 2>/dev/null || echo "Not linked to project"
    echo ""
    
    # Check health
    check_health
    echo ""
    
    # Show recent logs
    echo "📝 Recent Logs:"
    railway logs --tail 10 2>/dev/null || echo "No logs available"
    
    # Wait 5 seconds
    sleep 5
done