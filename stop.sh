#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 Stopping TradeSense...${NC}"

# Stop using PID files
if [ -f ".pids/backend.pid" ]; then
    pid=$(cat .pids/backend.pid)
    if ps -p $pid > /dev/null 2>&1; then
        kill $pid 2>/dev/null
        echo -e "${GREEN}✓ Stopped backend (PID: $pid)${NC}"
    fi
    rm -f .pids/backend.pid
fi

if [ -f ".pids/frontend.pid" ]; then
    pid=$(cat .pids/frontend.pid)
    if ps -p $pid > /dev/null 2>&1; then
        kill $pid 2>/dev/null
        echo -e "${GREEN}✓ Stopped frontend (PID: $pid)${NC}"
    fi
    rm -f .pids/frontend.pid
fi

# Kill by process name as backup
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null
pkill -f "vite" 2>/dev/null

# Cleanup
rm -f .pids/frontend.port 2>/dev/null

echo -e "${GREEN}✅ All services stopped${NC}"
echo -e "${YELLOW}Logs are available in the logs/ directory${NC}"
