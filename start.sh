#!/bin/bash

# TradeSense Unified Startup Script
# Combines the best features from all startup scripts
# Works reliably in development, testing, and demo environments

# ============================================================================
# Configuration
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Project settings
VENV_NAME="test_venv"
BACKEND_PORT=8000
FRONTEND_PORT=3001
FRONTEND_ALT_PORT=5173

# Files and directories
LOG_DIR="logs"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
PID_DIR=".pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
FRONTEND_PORT_FILE="$PID_DIR/frontend.port"

# ============================================================================
# Helper Functions
# ============================================================================

# Print colored output
print_status() {
    echo -e "${2}${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ ${1}${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        kill -9 $pid 2>/dev/null
        return 0
    fi
    return 1
}

# Check if port is available
is_port_available() {
    ! lsof -i:$1 >/dev/null 2>&1
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

print_status "🚀 TradeSense Startup Script v2.0" "$BLUE"
print_status "=================================" "$BLUE"

# Check if we're in the right directory
if [ ! -d "frontend" ] || [ ! -d "src/backend" ]; then
    print_error "This script must be run from the TradeSense root directory"
    print_info "Current directory: $(pwd)"
    exit 1
fi

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR" uploads temp

# ============================================================================
# Cleanup Previous Sessions
# ============================================================================

print_status "\n📧 Cleaning up previous sessions..." "$YELLOW"

# Kill existing processes using PID files
if [ -f "$BACKEND_PID_FILE" ]; then
    old_pid=$(cat "$BACKEND_PID_FILE")
    if ps -p $old_pid > /dev/null 2>&1; then
        kill $old_pid 2>/dev/null
        print_info "Stopped previous backend (PID: $old_pid)"
    fi
    rm -f "$BACKEND_PID_FILE"
fi

if [ -f "$FRONTEND_PID_FILE" ]; then
    old_pid=$(cat "$FRONTEND_PID_FILE")
    if ps -p $old_pid > /dev/null 2>&1; then
        kill $old_pid 2>/dev/null
        print_info "Stopped previous frontend (PID: $old_pid)"
    fi
    rm -f "$FRONTEND_PID_FILE"
fi

# Kill any remaining processes on our ports
kill_port $BACKEND_PORT && print_info "Cleared port $BACKEND_PORT"
kill_port $FRONTEND_PORT && print_info "Cleared port $FRONTEND_PORT"
kill_port $FRONTEND_ALT_PORT && print_info "Cleared port $FRONTEND_ALT_PORT"

# Kill by process name as fallback
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null
pkill -f "vite" 2>/dev/null

sleep 2

# ============================================================================
# Virtual Environment Setup
# ============================================================================

print_status "\n🐍 Setting up Python environment..." "$YELLOW"

# Check if virtual environment exists
if [ ! -d "$VENV_NAME" ] || [ ! -f "$VENV_NAME/bin/python" ]; then
    print_warning "Virtual environment not found. Creating new one..."
    python3 -m venv $VENV_NAME
    if [ $? -eq 0 ]; then
        print_success "Created virtual environment: $VENV_NAME"
    else
        print_error "Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
source $VENV_NAME/bin/activate
if [ $? -eq 0 ]; then
    print_success "Activated virtual environment"
else
    print_error "Failed to activate virtual environment"
    exit 1
fi

# Check for required packages (quick check)
if ! python -c "import fastapi" 2>/dev/null; then
    print_warning "Missing backend dependencies. Installing..."
    if [ -f "src/backend/requirements.txt" ]; then
        pip install -r src/backend/requirements.txt
    else
        pip install fastapi uvicorn sqlalchemy psycopg2-binary redis stripe
    fi
fi

# ============================================================================
# Backend Startup
# ============================================================================

print_status "\n🔧 Starting Backend Server..." "$YELLOW"

cd src/backend

# Start backend
nohup python -m uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "../../$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "../../$BACKEND_PID_FILE"

cd ../..

# Wait for backend to be ready
print_info "Waiting for backend to start..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
        print_success "Backend is running! (PID: $BACKEND_PID)"
        break
    fi
    sleep 1
    attempt=$((attempt + 1))
    echo -n "."
done
echo ""

if [ $attempt -eq $max_attempts ]; then
    print_error "Backend failed to start. Check $BACKEND_LOG for details"
    tail -20 "$BACKEND_LOG"
    exit 1
fi

# ============================================================================
# Frontend Startup
# ============================================================================

print_status "\n🎨 Starting Frontend Server..." "$YELLOW"

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_warning "Frontend dependencies not found. Installing..."
    npm install
fi

# Start frontend
nohup npm run dev > "../$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "../$FRONTEND_PID_FILE"

cd ..

# Wait and detect frontend port
print_info "Waiting for frontend to start..."
max_attempts=30
attempt=0
FRONTEND_URL=""

while [ $attempt -lt $max_attempts ]; do
    # Try to extract port from log
    if [ -f "$FRONTEND_LOG" ]; then
        port_line=$(grep -o "http://localhost:[0-9]*" "$FRONTEND_LOG" 2>/dev/null | head -1)
        if [ ! -z "$port_line" ]; then
            FRONTEND_URL=$port_line
            ACTUAL_FRONTEND_PORT=$(echo $FRONTEND_URL | grep -o "[0-9]*$")
            echo $ACTUAL_FRONTEND_PORT > "$FRONTEND_PORT_FILE"
            print_success "Frontend is running! (PID: $FRONTEND_PID)"
            break
        fi
    fi
    sleep 1
    attempt=$((attempt + 1))
    echo -n "."
done
echo ""

if [ -z "$FRONTEND_URL" ]; then
    print_error "Frontend failed to start. Check $FRONTEND_LOG for details"
    tail -20 "$FRONTEND_LOG"
    exit 1
fi

# ============================================================================
# Create Stop Script
# ============================================================================

cat > stop.sh << 'EOF'
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
EOF

chmod +x stop.sh

# ============================================================================
# Optional Features
# ============================================================================

# Check for Redis
if command_exists redis-server && ! pgrep -x "redis-server" > /dev/null; then
    print_info "Redis is installed but not running. Start with: redis-server"
fi

# Check for Stripe CLI
if command_exists stripe; then
    print_info "Stripe CLI detected. To test webhooks, run in another terminal:"
    print_info "  stripe listen --forward-to localhost:$BACKEND_PORT/api/v1/billing/webhook"
fi

# ============================================================================
# Success Summary
# ============================================================================

print_status "\n✨ TradeSense is running!" "$GREEN"
print_status "========================" "$GREEN"

echo -e "\n${WHITE}📍 Access URLs:${NC}"
echo -e "  ${CYAN}Frontend:${NC} ${GREEN}$FRONTEND_URL${NC}"
echo -e "  ${CYAN}Backend API:${NC} ${GREEN}http://localhost:$BACKEND_PORT${NC}"
echo -e "  ${CYAN}API Documentation:${NC} ${GREEN}http://localhost:$BACKEND_PORT/api/docs${NC}"

echo -e "\n${WHITE}👤 Test Credentials:${NC}"
echo -e "  ${CYAN}Email:${NC} demouser@test.com"
echo -e "  ${CYAN}Password:${NC} Demo@123456"

echo -e "\n${WHITE}🔗 Quick Links:${NC}"
echo -e "  ${CYAN}Home:${NC} $FRONTEND_URL"
echo -e "  ${CYAN}Pricing:${NC} $FRONTEND_URL/pricing"
echo -e "  ${CYAN}Login:${NC} $FRONTEND_URL/login"
echo -e "  ${CYAN}Billing:${NC} $FRONTEND_URL/billing ${YELLOW}(after login)${NC}"

echo -e "\n${WHITE}💳 Test Credit Cards:${NC}"
echo -e "  ${CYAN}Success:${NC} 4242 4242 4242 4242"
echo -e "  ${CYAN}3D Secure:${NC} 4000 0025 0000 3155"
echo -e "  ${CYAN}Declined:${NC} 4000 0000 0000 9995"
echo -e "  ${YELLOW}Use any future date, any CVC, any ZIP${NC}"

echo -e "\n${WHITE}📝 Useful Commands:${NC}"
echo -e "  ${CYAN}View logs:${NC} tail -f logs/backend.log"
echo -e "  ${CYAN}Stop all:${NC} ./stop.sh"
echo -e "  ${CYAN}Check health:${NC} curl http://localhost:$BACKEND_PORT/health"

# Try to open browser
if [ "$(uname)" == "Darwin" ]; then
    # macOS
    open "$FRONTEND_URL" 2>/dev/null
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    # Linux
    if command_exists xdg-open; then
        xdg-open "$FRONTEND_URL" 2>/dev/null &
    elif command_exists gnome-open; then
        gnome-open "$FRONTEND_URL" 2>/dev/null &
    fi
fi

print_status "\n🎉 Enjoy using TradeSense!" "$PURPLE"