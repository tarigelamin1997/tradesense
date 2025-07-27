#!/bin/bash

# TradeSense Production Deployment Script
# Complete deployment automation with safety checks and rollback capabilities

set -e

# Configuration
ENVIRONMENT="${1:-production}"
VERSION="${2:-latest}"
DRY_RUN="${DRY_RUN:-false}"
SKIP_TESTS="${SKIP_TESTS:-false}"
SKIP_BACKUP="${SKIP_BACKUP:-false}"
NAMESPACE="tradesense"
REGISTRY="ghcr.io/tradesense"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
LOG_FILE="deployment-$(date +%Y%m%d_%H%M%S).log"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

# Functions
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Pre-deployment checks
pre_deployment_checks() {
    print_status "Running pre-deployment checks..."
    
    # Check kubectl connection
    if ! kubectl cluster-info &>/dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check namespace exists
    if ! kubectl get namespace $NAMESPACE &>/dev/null; then
        print_error "Namespace $NAMESPACE does not exist"
        exit 1
    fi
    
    # Check current deployment status
    local unhealthy_pods=$(kubectl get pods -n $NAMESPACE -o json | jq '.items[] | select(.status.phase != "Running") | .metadata.name' | wc -l)
    if [ "$unhealthy_pods" -gt 0 ]; then
        print_warning "Found $unhealthy_pods unhealthy pods"
        kubectl get pods -n $NAMESPACE | grep -v Running
        
        if [ "$FORCE_DEPLOY" != "true" ]; then
            read -p "Continue with deployment? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
    
    print_success "Pre-deployment checks passed"
}

# Run tests
run_tests() {
    if [ "$SKIP_TESTS" = "true" ]; then
        print_warning "Skipping tests (SKIP_TESTS=true)"
        return
    fi
    
    print_status "Running tests..."
    
    # Backend tests
    print_status "Running backend tests..."
    cd src/backend
    python -m pytest tests/ -v --tb=short || {
        print_error "Backend tests failed"
        exit 1
    }
    cd ../..
    
    # Frontend tests
    print_status "Running frontend tests..."
    cd frontend
    npm test || {
        print_error "Frontend tests failed"
        exit 1
    }
    cd ..
    
    print_success "All tests passed"
}

# Create backup
create_backup() {
    if [ "$SKIP_BACKUP" = "true" ]; then
        print_warning "Skipping backup (SKIP_BACKUP=true)"
        return
    fi
    
    print_status "Creating production backup..."
    
    # Trigger backup job
    kubectl create job --from=cronjob/postgres-backup postgres-backup-manual-$(date +%Y%m%d%H%M%S) -n $NAMESPACE
    
    # Wait for backup to complete
    print_status "Waiting for backup to complete..."
    kubectl wait --for=condition=complete job/postgres-backup-manual-* -n $NAMESPACE --timeout=300s
    
    print_success "Backup completed"
}

# Build and push images
build_images() {
    print_status "Building and pushing Docker images..."
    
    # Backend
    print_status "Building backend image..."
    docker build -f src/backend/Dockerfile.production -t $REGISTRY/backend:$VERSION src/backend/
    
    if [ "$DRY_RUN" != "true" ]; then
        docker push $REGISTRY/backend:$VERSION
        docker tag $REGISTRY/backend:$VERSION $REGISTRY/backend:latest
        docker push $REGISTRY/backend:latest
    fi
    
    # Frontend
    print_status "Building frontend image..."
    docker build -f frontend/Dockerfile.production -t $REGISTRY/frontend:$VERSION frontend/
    
    if [ "$DRY_RUN" != "true" ]; then
        docker push $REGISTRY/frontend:$VERSION
        docker tag $REGISTRY/frontend:$VERSION $REGISTRY/frontend:latest
        docker push $REGISTRY/frontend:latest
    fi
    
    print_success "Images built and pushed"
}

# Deploy to Kubernetes
deploy_to_kubernetes() {
    print_status "Deploying to Kubernetes..."
    
    # Update image tags
    sed -i "s|image: tradesense/backend:.*|image: $REGISTRY/backend:$VERSION|g" k8s/backend.yaml
    sed -i "s|image: tradesense/frontend:.*|image: $REGISTRY/frontend:$VERSION|g" k8s/frontend.yaml
    
    if [ "$DRY_RUN" = "true" ]; then
        print_warning "DRY RUN: Would apply the following changes:"
        kubectl diff -f k8s/ || true
        return
    fi
    
    # Apply database migrations
    print_status "Running database migrations..."
    kubectl exec -it deployment/backend -n $NAMESPACE -- alembic upgrade head
    
    # Deploy backend with rolling update
    print_status "Deploying backend..."
    kubectl apply -f k8s/backend.yaml
    kubectl rollout status deployment/backend -n $NAMESPACE --timeout=300s
    
    # Deploy frontend with rolling update
    print_status "Deploying frontend..."
    kubectl apply -f k8s/frontend.yaml
    kubectl rollout status deployment/frontend -n $NAMESPACE --timeout=300s
    
    # Update other resources
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/ingress.yaml
    
    print_success "Deployment completed"
}

# Run smoke tests
run_smoke_tests() {
    print_status "Running smoke tests..."
    
    # Wait for services to stabilize
    sleep 30
    
    # Health check
    if ! curl -f https://api.tradesense.com/api/v1/monitoring/health; then
        print_error "Health check failed"
        return 1
    fi
    
    # API endpoints
    local endpoints=(
        "/api/v1/monitoring/health"
        "/api/v1/analytics/dashboard"
        "/api/v1/trades"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f "https://api.tradesense.com$endpoint" -H "Authorization: Bearer $TEST_TOKEN"; then
            print_success "Endpoint $endpoint OK"
        else
            print_error "Endpoint $endpoint FAILED"
            return 1
        fi
    done
    
    print_success "Smoke tests passed"
}

# Monitor deployment
monitor_deployment() {
    print_status "Monitoring deployment for 5 minutes..."
    
    local end_time=$(($(date +%s) + 300))
    local error_count=0
    
    while [ $(date +%s) -lt $end_time ]; do
        # Check pod status
        local unhealthy=$(kubectl get pods -n $NAMESPACE -o json | jq '.items[] | select(.status.phase != "Running") | .metadata.name' | wc -l)
        
        if [ "$unhealthy" -gt 0 ]; then
            print_warning "Unhealthy pods detected: $unhealthy"
            error_count=$((error_count + 1))
        fi
        
        # Check error rate
        local error_rate=$(curl -s http://prometheus:9090/api/v1/query?query=rate\(tradesense_http_requests_total\{status=~\"5..\"\}\[1m\]\) | jq '.data.result[0].value[1]' | sed 's/"//g')
        
        if (( $(echo "$error_rate > 0.01" | bc -l) )); then
            print_warning "High error rate detected: $error_rate"
            error_count=$((error_count + 1))
        fi
        
        if [ $error_count -gt 5 ]; then
            print_error "Too many errors detected, consider rollback"
            return 1
        fi
        
        sleep 30
    done
    
    print_success "Deployment monitoring completed successfully"
}

# Rollback function
rollback() {
    print_error "Deployment failed, initiating rollback..."
    
    kubectl rollout undo deployment/backend -n $NAMESPACE
    kubectl rollout undo deployment/frontend -n $NAMESPACE
    
    kubectl rollout status deployment/backend -n $NAMESPACE
    kubectl rollout status deployment/frontend -n $NAMESPACE
    
    print_warning "Rollback completed"
    exit 1
}

# Main deployment flow
main() {
    echo "========================================"
    echo "TradeSense Production Deployment"
    echo "========================================"
    echo "Environment: $ENVIRONMENT"
    echo "Version: $VERSION"
    echo "Dry Run: $DRY_RUN"
    echo ""
    
    # Trap errors for rollback
    trap rollback ERR
    
    # Deployment steps
    pre_deployment_checks
    run_tests
    create_backup
    build_images
    deploy_to_kubernetes
    
    if [ "$DRY_RUN" != "true" ]; then
        run_smoke_tests || rollback
        monitor_deployment || rollback
    fi
    
    # Success notification
    print_success "Deployment completed successfully!"
    
    # Send notifications
    if [ "$DRY_RUN" != "true" ]; then
        # Slack notification
        if [ -n "$SLACK_WEBHOOK" ]; then
            curl -X POST -H 'Content-type: application/json' \
                --data "{\"text\":\"✅ TradeSense $VERSION deployed to $ENVIRONMENT successfully\"}" \
                "$SLACK_WEBHOOK"
        fi
        
        # Update status page
        curl -X POST https://api.statuspage.io/v1/pages/$STATUSPAGE_ID/incidents \
            -H "Authorization: OAuth $STATUSPAGE_API_KEY" \
            -d "incident[name]=Deployment Complete" \
            -d "incident[status]=resolved" \
            -d "incident[body]=Version $VERSION deployed successfully"
    fi
    
    # Cleanup
    trap - ERR
    
    echo ""
    echo "Deployment Summary:"
    echo "==================="
    echo "Version: $VERSION"
    echo "Start Time: $START_TIME"
    echo "End Time: $(date)"
    echo "Log File: $LOG_FILE"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --force)
            FORCE_DEPLOY=true
            shift
            ;;
        --version)
            VERSION=$2
            shift 2
            ;;
        --help)
            echo "Usage: $0 [environment] [version] [options]"
            echo ""
            echo "Options:"
            echo "  --dry-run       Show what would be deployed without making changes"
            echo "  --skip-tests    Skip running tests"
            echo "  --skip-backup   Skip creating backup"
            echo "  --force         Force deployment even with unhealthy pods"
            echo "  --version       Specify version tag"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            if [ -z "$ENVIRONMENT" ]; then
                ENVIRONMENT=$1
            elif [ -z "$VERSION" ]; then
                VERSION=$1
            fi
            shift
            ;;
    esac
done

# Record start time
START_TIME=$(date)

# Run main deployment
main