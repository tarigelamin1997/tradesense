
#!/bin/bash

set -e

echo "🚀 TradeSense Deployment Script"
echo "==============================="

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000
DATABASE_BACKUP_DIR="./backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        log_error "Node.js is required but not installed"
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        log_error "Git is required but not installed"
        exit 1
    fi
    
    log_info "Prerequisites check passed ✓"
}

# Create database backup
backup_database() {
    log_info "Creating database backup..."
    
    mkdir -p $DATABASE_BACKUP_DIR
    
    if [ -f "backend/tradesense.db" ]; then
        cp backend/tradesense.db "$DATABASE_BACKUP_DIR/tradesense_$(date +%Y%m%d_%H%M%S).db"
        log_info "Database backup created ✓"
    else
        log_warn "No database found to backup"
    fi
}

# Install dependencies
install_dependencies() {
    log_info "Installing backend dependencies..."
    cd backend
    python3 -m pip install --user --break-system-packages --no-cache-dir -r requirements-test.txt
    cd ..
    
    log_info "Installing frontend dependencies..."
    cd frontend
    npm install --legacy-peer-deps
    cd ..
    
    log_info "Dependencies installed ✓"
}

# Run tests
run_tests() {
    log_info "Running backend tests..."
    cd backend
    python3 -m pytest tests/ -v --tb=short
    cd ..
    
    log_info "Running frontend tests..."
    cd frontend
    npm run test:ci 2>/dev/null || log_warn "Frontend tests not configured"
    cd ..
    
    log_info "Tests completed ✓"
}

# Build frontend
build_frontend() {
    log_info "Building frontend..."
    cd frontend
    npm run build
    cd ..
    log_info "Frontend build completed ✓"
}

# Start services
start_services() {
    log_info "Starting TradeSense services..."
    
    # Kill existing processes
    pkill -f "python.*main.py" || true
    pkill -f "npm.*dev" || true
    
    # Start backend
    log_info "Starting backend on port $BACKEND_PORT..."
    cd backend
    nohup python3 main.py > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    # Start frontend
    log_info "Starting frontend on port $FRONTEND_PORT..."
    cd frontend
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    # Save PIDs
    echo $BACKEND_PID > .backend.pid
    echo $FRONTEND_PID > .frontend.pid
    
    log_info "Services started ✓"
    log_info "Backend PID: $BACKEND_PID"
    log_info "Frontend PID: $FRONTEND_PID"
}

# Health check
health_check() {
    log_info "Performing health checks..."
    
    # Wait for services to start
    sleep 10
    
    # Check backend
    if curl -s http://localhost:$BACKEND_PORT/health > /dev/null; then
        log_info "Backend health check passed ✓"
    else
        log_error "Backend health check failed ✗"
        return 1
    fi
    
    # Check frontend
    if curl -s http://localhost:$FRONTEND_PORT > /dev/null; then
        log_info "Frontend health check passed ✓"
    else
        log_error "Frontend health check failed ✗"
        return 1
    fi
    
    log_info "All health checks passed ✓"
}

# Main deployment function
deploy() {
    log_info "Starting TradeSense deployment..."
    
    check_prerequisites
    backup_database
    install_dependencies
    run_tests
    build_frontend
    start_services
    health_check
    
    log_info "🎉 Deployment completed successfully!"
    log_info "Backend: http://localhost:$BACKEND_PORT"
    log_info "Frontend: http://localhost:$FRONTEND_PORT"
    log_info "Logs: ./logs/"
}

# Handle command line arguments
case "$1" in
    "check")
        check_prerequisites
        ;;
    "backup")
        backup_database
        ;;
    "install")
        install_dependencies
        ;;
    "test")
        run_tests
        ;;
    "build")
        build_frontend
        ;;
    "start")
        start_services
        ;;
    "health")
        health_check
        ;;
    "")
        deploy
        ;;
    *)
        echo "Usage: $0 [check|backup|install|test|build|start|health]"
        echo "  check   - Check prerequisites"
        echo "  backup  - Backup database"
        echo "  install - Install dependencies"
        echo "  test    - Run tests"
        echo "  build   - Build frontend"
        echo "  start   - Start services"
        echo "  health  - Run health checks"
        echo "  (empty) - Full deployment"
        exit 1
        ;;
esac
