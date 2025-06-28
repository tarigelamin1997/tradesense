
#!/bin/bash

# TradeSense Deployment Script
# Handles deployment to Replit with comprehensive checks

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-staging}"
VERSION="${2:-$(date +%Y%m%d-%H%M%S)}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Deployment functions
check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository"
        exit 1
    fi
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        log_warning "You have uncommitted changes"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check required tools
    for tool in curl python3 npm; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool is required but not installed"
            exit 1
        fi
    done
    
    log_success "Prerequisites check passed"
}

run_tests() {
    log_info "Running test suite..."
    
    cd "$PROJECT_ROOT"
    
    # Backend tests
    log_info "Running backend tests..."
    cd backend
    if ! python -m pytest --quiet; then
        log_error "Backend tests failed"
        exit 1
    fi
    cd ..
    
    # Frontend tests
    log_info "Running frontend tests..."
    cd frontend
    if ! npm test -- --watchAll=false; then
        log_error "Frontend tests failed"
        exit 1
    fi
    cd ..
    
    log_success "All tests passed"
}

build_frontend() {
    log_info "Building frontend..."
    
    cd "$PROJECT_ROOT/frontend"
    
    # Install dependencies
    npm ci
    
    # Build production bundle
    npm run build
    
    # Verify build output
    if [ ! -d "dist" ]; then
        log_error "Frontend build failed - no dist directory"
        exit 1
    fi
    
    log_success "Frontend build completed"
    cd ..
}

prepare_deployment() {
    log_info "Preparing deployment package..."
    
    cd "$PROJECT_ROOT"
    
    # Create deployment directory
    rm -rf deployment-temp
    mkdir -p deployment-temp
    
    # Copy backend files
    cp -r backend/* deployment-temp/
    
    # Copy frontend build
    mkdir -p deployment-temp/static
    cp -r frontend/dist/* deployment-temp/static/
    
    # Create deployment manifest
    cat > deployment-temp/deployment-info.json << EOF
{
    "version": "$VERSION",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "commit": "$(git rev-parse HEAD)",
    "branch": "$(git branch --show-current)",
    "environment": "$ENVIRONMENT",
    "components": {
        "backend": "FastAPI",
        "frontend": "React + Vite",
        "database": "SQLite"
    }
}
EOF
    
    log_success "Deployment package prepared"
}

deploy_to_replit() {
    log_info "Deploying to Replit ($ENVIRONMENT)..."
    
    cd "$PROJECT_ROOT"
    
    # Create backup
    log_info "Creating backup..."
    if [ -f "tradesense.db" ]; then
        cp tradesense.db "tradesense.db.backup.$(date +%Y%m%d-%H%M%S)"
    fi
    
    # Copy deployment files
    log_info "Copying files..."
    cp -r deployment-temp/* .
    
    # Install/update backend dependencies
    log_info "Installing backend dependencies..."
    cd backend
    python -m pip install --user --upgrade -r requirements.txt
    cd ..
    
    # Update database schema if needed
    log_info "Updating database..."
    cd backend
    python -c "
from database.database import init_db
init_db()
print('Database updated successfully')
"
    cd ..
    
    # Cleanup
    rm -rf deployment-temp
    
    log_success "Deployment to Replit completed"
}

run_health_checks() {
    log_info "Running health checks..."
    
    # Start the application in background for testing
    cd "$PROJECT_ROOT"
    
    # Test backend health
    log_info "Testing backend health..."
    cd backend
    timeout 30 python -c "
import sys
import time
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)
max_attempts = 10
for i in range(max_attempts):
    try:
        response = client.get('/health')
        if response.status_code == 200:
            print('Backend health check passed')
            sys.exit(0)
    except:
        pass
    time.sleep(1)
print('Backend health check failed')
sys.exit(1)
" || {
        log_error "Backend health check failed"
        exit 1
    }
    cd ..
    
    # Test database connectivity
    log_info "Testing database connectivity..."
    cd backend
    python -c "
from database.database import get_db
from sqlalchemy import text

try:
    db = next(get_db())
    result = db.execute(text('SELECT 1')).fetchone()
    if result:
        print('Database connectivity check passed')
    else:
        raise Exception('No result')
except Exception as e:
    print(f'Database connectivity check failed: {e}')
    exit(1)
" || {
        log_error "Database connectivity check failed"
        exit 1
    }
    cd ..
    
    log_success "All health checks passed"
}

rollback() {
    log_info "Rolling back deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Restore database backup if exists
    LATEST_BACKUP=$(ls -t tradesense.db.backup.* 2>/dev/null | head -n1 || echo "")
    if [ ! -z "$LATEST_BACKUP" ]; then
        log_info "Restoring database backup: $LATEST_BACKUP"
        cp "$LATEST_BACKUP" tradesense.db
    fi
    
    # Reset to previous git state
    log_info "Resetting to previous git state..."
    git reset --hard HEAD~1
    
    log_success "Rollback completed"
}

show_deployment_summary() {
    log_info "Deployment Summary"
    echo "=========================="
    echo "Environment: $ENVIRONMENT"
    echo "Version: $VERSION"
    echo "Timestamp: $(date)"
    echo "Commit: $(git rev-parse HEAD)"
    echo "Branch: $(git branch --show-current)"
    echo "=========================="
}

# Main deployment flow
main() {
    case "${1:-deploy}" in
        deploy)
            log_info "Starting TradeSense deployment to $ENVIRONMENT"
            check_prerequisites
            run_tests
            build_frontend
            prepare_deployment
            deploy_to_replit
            run_health_checks
            show_deployment_summary
            log_success "Deployment completed successfully!"
            ;;
        rollback)
            log_warning "Initiating rollback..."
            rollback
            log_success "Rollback completed!"
            ;;
        test)
            log_info "Running tests only..."
            check_prerequisites
            run_tests
            log_success "Tests completed!"
            ;;
        *)
            echo "Usage: $0 {deploy|rollback|test} [environment] [version]"
            echo "  deploy    - Full deployment (default)"
            echo "  rollback  - Rollback to previous version"
            echo "  test      - Run tests only"
            echo ""
            echo "Examples:"
            echo "  $0 deploy staging"
            echo "  $0 deploy production v1.2.3"
            echo "  $0 rollback"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
