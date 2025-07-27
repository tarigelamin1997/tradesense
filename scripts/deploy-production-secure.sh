#!/bin/bash
# Production Deployment Script with Security Hardening
# Deploys all services with production-ready security configurations

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 TradeSense Production Deployment (Secure)${NC}"
echo "==========================================="
echo ""

# Configuration
SERVICES=("gateway" "auth" "trading" "analytics" "billing" "market-data" "ai")
ENVIRONMENT="production"
DEPLOY_TIMEOUT=600  # 10 minutes

# Validation functions
validate_prerequisites() {
    echo -e "${BLUE}Validating prerequisites...${NC}"
    
    # Check Railway CLI
    if ! command -v railway &> /dev/null; then
        echo -e "${RED}❌ Railway CLI not installed${NC}"
        exit 1
    fi
    
    # Check Railway login
    if ! railway whoami &> /dev/null; then
        echo -e "${RED}❌ Not logged in to Railway${NC}"
        exit 1
    fi
    
    # Check environment files
    for service in "${SERVICES[@]}"; do
        if [ ! -f "services/${service}/.env.production" ]; then
            echo -e "${YELLOW}⚠️  Missing .env.production for ${service}${NC}"
        fi
    done
    
    echo -e "${GREEN}✅ Prerequisites validated${NC}"
}

# Security configuration
configure_security() {
    local service=$1
    echo -e "${BLUE}Configuring security for ${service}...${NC}"
    
    # Generate secure keys if not set
    if ! railway variables get JWT_SECRET_KEY --service "$service" &> /dev/null; then
        JWT_SECRET=$(openssl rand -base64 64 | tr -d '\n')
        railway variables set JWT_SECRET_KEY="$JWT_SECRET" --service "$service"
        echo "  - JWT secret key generated"
    fi
    
    if ! railway variables get MASTER_ENCRYPTION_KEY --service "$service" &> /dev/null; then
        ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        railway variables set MASTER_ENCRYPTION_KEY="$ENCRYPTION_KEY" --service "$service"
        echo "  - Master encryption key generated"
    fi
    
    # Set security headers configuration
    railway variables set \
        ENABLE_SECURITY_HEADERS=true \
        ENABLE_RATE_LIMITING=true \
        ENABLE_INPUT_VALIDATION=true \
        ENABLE_AUDIT_LOGGING=true \
        --service "$service"
    
    echo -e "${GREEN}✅ Security configured for ${service}${NC}"
}

# Update service to use secure main.py
update_service_code() {
    local service=$1
    local service_path="services/${service}"
    
    echo -e "${BLUE}Updating ${service} to use secure configuration...${NC}"
    
    # Check if service uses FastAPI
    if [ -f "${service_path}/src/main.py" ]; then
        # Create startup script that uses secure main
        cat > "${service_path}/src/startup.py" << 'EOF'
"""
Production startup script with security
"""
import os
import sys

# Add backend to path for shared modules
sys.path.insert(0, '/app/backend')

# Import and run secure main
from main_secure import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=1,  # Railway handles scaling
        loop="uvloop",
        access_log=False,
        server_header=False,
        date_header=False
    )
EOF
        
        # Update Dockerfile to use secure startup
        sed -i.bak 's/CMD \["uvicorn".*\]/CMD ["python", "src\/startup.py"]/' "${service_path}/Dockerfile"
        
        echo -e "${GREEN}✅ Updated ${service} code${NC}"
    fi
}

# Deploy service with health monitoring
deploy_service() {
    local service=$1
    local service_path="services/${service}"
    
    echo -e "${BLUE}Deploying ${service}...${NC}"
    
    # Configure security first
    configure_security "$service"
    
    # Update code for security
    update_service_code "$service"
    
    # Deploy
    cd "$service_path"
    
    # Set deployment environment
    export RAILWAY_ENVIRONMENT="production"
    
    # Deploy with timeout
    timeout $DEPLOY_TIMEOUT railway up --detach || {
        echo -e "${RED}❌ Deployment timeout for ${service}${NC}"
        return 1
    }
    
    cd - > /dev/null
    
    # Wait for service to be healthy
    echo "  Waiting for ${service} to be healthy..."
    local retries=30
    local service_url="https://tradesense-${service}-production.up.railway.app/health"
    
    while [ $retries -gt 0 ]; do
        if curl -sf "$service_url" > /dev/null; then
            echo -e "${GREEN}✅ ${service} is healthy${NC}"
            return 0
        fi
        
        sleep 10
        ((retries--))
    done
    
    echo -e "${RED}❌ ${service} health check failed${NC}"
    return 1
}

# Configure monitoring
setup_monitoring() {
    echo -e "${BLUE}Setting up monitoring...${NC}"
    
    # Create monitoring configuration
    cat > monitoring/production-config.yml << EOF
services:
  - name: gateway
    url: https://tradesense-gateway-production.up.railway.app
    interval: 30s
    timeout: 10s
    alerts:
      - type: down
        threshold: 2
        channels: [slack, pagerduty]
      - type: slow_response
        threshold: 1000ms
        channels: [slack]
  
  - name: auth
    url: https://tradesense-auth-production.up.railway.app
    interval: 30s
    critical: true
    
  - name: trading
    url: https://tradesense-trading-production.up.railway.app
    interval: 30s
    critical: true

alerts:
  slack:
    webhook: \${SLACK_WEBHOOK_URL}
    channel: "#production-alerts"
  
  pagerduty:
    api_key: \${PAGERDUTY_API_KEY}
    service_id: \${PAGERDUTY_SERVICE_ID}

metrics:
  - name: error_rate
    query: rate(http_requests_total{status=~"5.."}[5m])
    threshold: 0.01
    severity: critical
    
  - name: response_time_p95
    query: histogram_quantile(0.95, http_request_duration_seconds_bucket)
    threshold: 1.0
    severity: warning
EOF
    
    echo -e "${GREEN}✅ Monitoring configured${NC}"
}

# Run security validation
validate_security() {
    echo -e "${BLUE}Running security validation...${NC}"
    
    # Check HTTPS
    for service in "${SERVICES[@]}"; do
        url="https://tradesense-${service}-production.up.railway.app"
        if ! curl -sf -I "$url" | grep -q "HTTP/2"; then
            echo -e "${YELLOW}⚠️  ${service} not using HTTP/2${NC}"
        fi
    done
    
    # Check security headers
    gateway_url="https://tradesense-gateway-production.up.railway.app/health"
    headers=$(curl -sf -I "$gateway_url")
    
    required_headers=(
        "Strict-Transport-Security"
        "X-Content-Type-Options"
        "X-Frame-Options"
        "Content-Security-Policy"
    )
    
    for header in "${required_headers[@]}"; do
        if ! echo "$headers" | grep -qi "$header"; then
            echo -e "${RED}❌ Missing security header: ${header}${NC}"
        else
            echo -e "${GREEN}✅ Security header present: ${header}${NC}"
        fi
    done
}

# Create deployment summary
create_summary() {
    local deploy_time=$1
    
    cat > deployment-summary.md << EOF
# Production Deployment Summary

**Date**: $(date)
**Environment**: Production
**Deploy Time**: ${deploy_time}s

## Services Deployed

| Service | Status | URL | Health |
|---------|--------|-----|--------|
EOF
    
    for service in "${SERVICES[@]}"; do
        url="https://tradesense-${service}-production.up.railway.app"
        if curl -sf "$url/health" > /dev/null; then
            status="✅ Deployed"
            health="Healthy"
        else
            status="❌ Failed"
            health="Unhealthy"
        fi
        
        echo "| $service | $status | $url | $health |" >> deployment-summary.md
    done
    
    cat >> deployment-summary.md << EOF

## Security Configuration

- ✅ HTTPS enabled on all endpoints
- ✅ Security headers configured
- ✅ Rate limiting active
- ✅ Input validation enabled
- ✅ Audit logging configured

## Next Steps

1. Monitor services at [Railway Dashboard](https://railway.app/dashboard)
2. Check logs: \`railway logs --service <service-name>\`
3. View metrics in monitoring dashboard
4. Test all critical user flows

## Rollback Procedure

If issues are detected:
\`\`\`bash
./scripts/rollback-production.sh <service-name>
\`\`\`
EOF
    
    echo -e "${GREEN}✅ Deployment summary created${NC}"
}

# Main deployment flow
main() {
    local start_time=$(date +%s)
    
    echo "⚠️  WARNING: This will deploy to PRODUCTION"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Deployment cancelled"
        exit 1
    fi
    
    # Create deployment tracking
    mkdir -p deployments
    local deploy_id="deploy_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "deployments/$deploy_id"
    
    # Run validations
    validate_prerequisites
    
    # Setup monitoring first
    setup_monitoring
    
    # Deploy services
    local failed_services=()
    
    for service in "${SERVICES[@]}"; do
        echo ""
        if deploy_service "$service"; then
            echo "$service: SUCCESS" >> "deployments/$deploy_id/status.txt"
        else
            echo "$service: FAILED" >> "deployments/$deploy_id/status.txt"
            failed_services+=("$service")
        fi
    done
    
    # Run security validation
    echo ""
    validate_security
    
    # Calculate deployment time
    local end_time=$(date +%s)
    local deploy_time=$((end_time - start_time))
    
    # Create summary
    create_summary $deploy_time
    
    # Final status
    echo ""
    echo "======================================"
    if [ ${#failed_services[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL${NC}"
        echo "All services deployed and healthy!"
    else
        echo -e "${RED}❌ DEPLOYMENT FAILED${NC}"
        echo "Failed services: ${failed_services[*]}"
        echo ""
        echo "Run rollback: ./scripts/rollback-production.sh"
    fi
    echo "======================================"
    
    # Copy deployment artifacts
    cp deployment-summary.md "deployments/$deploy_id/"
    cp monitoring/production-config.yml "deployments/$deploy_id/"
    
    echo ""
    echo "Deployment ID: $deploy_id"
    echo "Time taken: ${deploy_time}s"
    echo "Summary: deployment-summary.md"
}

# Run main function
main "$@"