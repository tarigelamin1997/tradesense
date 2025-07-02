
#!/bin/bash

# TradeSense Production Deployment Script
# Automated deployment with health checks and rollback

set -e  # Exit on any error

# Configuration
DEPLOYMENT_ENV=${1:-production}
HEALTH_CHECK_URL="http://localhost:8000/api/health"
FRONTEND_URL="http://localhost:3000"
MAX_RETRIES=30
RETRY_INTERVAL=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check if required files exist
    if [[ ! -f "backend/main.py" ]]; then
        error "Backend main.py not found!"
        exit 1
    fi
    
    if [[ ! -f "frontend/package.json" ]]; then
        error "Frontend package.json not found!"
        exit 1
    fi
    
    # Check Python dependencies
    log "Checking Python environment..."
    python3 -c "import fastapi, uvicorn, sqlalchemy" || {
        error "Missing Python dependencies!"
        exit 1
    }
    
    # Check Node.js dependencies
    log "Checking Node.js environment..."
    if [[ ! -d "frontend/node_modules" ]]; then
        warning "Node modules not found, will install..."
    fi
    
    success "Pre-deployment checks passed"
}

# Stop existing services
stop_services() {
    log "Stopping existing services..."
    
    # Kill any existing backend processes
    pkill -f "python.*main.py" || true
    pkill -f "uvicorn" || true
    
    # Kill any existing frontend processes
    pkill -f "npm.*dev" || true
    pkill -f "vite" || true
    
    sleep 3
    success "Services stopped"
}

# Deploy backend
deploy_backend() {
    log "Deploying backend..."
    
    cd backend
    
    # Install/update dependencies
    python3 -m pip install --user --break-system-packages --no-cache-dir \
        fastapi uvicorn python-multipart sqlalchemy psycopg2-binary \
        python-jose[cryptography] passlib[bcrypt] python-dateutil pandas cachetools
    
    # Initialize database
    log "Initializing database..."
    python3 -c "
from backend.db.connection import engine, Base
from backend.models.trade import Trade
from backend.models.user import User
from backend.models.feature_request import FeatureRequest
Base.metadata.create_all(bind=engine)
print('✅ Database initialized')
" || {
        error "Database initialization failed!"
        exit 1
    }
    
    # Start backend service
    log "Starting backend service..."
    nohup python3 main.py > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../logs/backend.pid
    
    cd ..
    success "Backend deployed (PID: $BACKEND_PID)"
}

# Deploy frontend
deploy_frontend() {
    log "Deploying frontend..."
    
    cd frontend
    
    # Install dependencies
    npm install --legacy-peer-deps
    
    # Start frontend service
    log "Starting frontend service..."
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    
    cd ..
    success "Frontend deployed (PID: $FRONTEND_PID)"
}

# Health checks
health_check() {
    log "Running health checks..."
    
    # Backend health check
    for i in $(seq 1 $MAX_RETRIES); do
        if curl -s "$HEALTH_CHECK_URL" > /dev/null; then
            success "Backend health check passed"
            break
        fi
        
        if [[ $i -eq $MAX_RETRIES ]]; then
            error "Backend health check failed after $MAX_RETRIES attempts"
            return 1
        fi
        
        log "Backend not ready, retrying in ${RETRY_INTERVAL}s... ($i/$MAX_RETRIES)"
        sleep $RETRY_INTERVAL
    done
    
    # Frontend health check
    for i in $(seq 1 $MAX_RETRIES); do
        if curl -s "$FRONTEND_URL" > /dev/null; then
            success "Frontend health check passed"
            break
        fi
        
        if [[ $i -eq $MAX_RETRIES ]]; then
            error "Frontend health check failed after $MAX_RETRIES attempts"
            return 1
        fi
        
        log "Frontend not ready, retrying in ${RETRY_INTERVAL}s... ($i/$MAX_RETRIES)"
        sleep $RETRY_INTERVAL
    done
    
    success "All health checks passed"
}

# Post-deployment tasks
post_deployment() {
    log "Running post-deployment tasks..."
    
    # Create deployment record
    TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
    echo "Deployment completed at: $(date)" > "logs/deployment_${TIMESTAMP}.log"
    
    # Log deployment info
    cat >> "logs/deployment_${TIMESTAMP}.log" << EOF
Environment: $DEPLOYMENT_ENV
Backend PID: $(cat logs/backend.pid 2>/dev/null || echo "N/A")
Frontend PID: $(cat logs/frontend.pid 2>/dev/null || echo "N/A")
Git Commit: $(git rev-parse HEAD 2>/dev/null || echo "N/A")
EOF
    
    success "Post-deployment tasks completed"
}

# Rollback function
rollback() {
    error "Deployment failed, initiating rollback..."
    
    # Stop current services
    if [[ -f "logs/backend.pid" ]]; then
        kill $(cat logs/backend.pid) 2>/dev/null || true
    fi
    
    if [[ -f "logs/frontend.pid" ]]; then
        kill $(cat logs/frontend.pid) 2>/dev/null || true
    fi
    
    # Start rollback script
    if [[ -f "scripts/rollback.sh" ]]; then
        bash scripts/rollback.sh
    fi
    
    error "Rollback completed"
    exit 1
}

# Main deployment flow
main() {
    log "🚀 Starting TradeSense deployment to $DEPLOYMENT_ENV"
    
    # Create logs directory
    mkdir -p logs
    
    # Set trap for rollback on failure
    trap rollback ERR
    
    pre_deployment_checks
    stop_services
    deploy_backend
    deploy_frontend
    health_check
    post_deployment
    
    success "🎉 Deployment completed successfully!"
    log "Backend: $HEALTH_CHECK_URL"
    log "Frontend: $FRONTEND_URL"
    log "Logs: $(pwd)/logs/"
}

# Run main function
main "$@"
