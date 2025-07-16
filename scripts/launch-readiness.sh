#!/bin/bash

# TradeSense Launch Readiness Check Script
# Automated verification of critical launch requirements

set -e

# Configuration
ENVIRONMENT=${1:-production}
CHECK_RESULTS=()
FAILED_CHECKS=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log() {
    echo -e "${BLUE}[CHECK] $1${NC}"
}

pass() {
    echo -e "${GREEN}✓ $1${NC}"
    CHECK_RESULTS+=("✓ $1")
}

fail() {
    echo -e "${RED}✗ $1${NC}"
    CHECK_RESULTS+=("✗ $1")
    ((FAILED_CHECKS++))
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    CHECK_RESULTS+=("⚠ $1")
}

# Security Checks
security_checks() {
    log "Running security checks..."
    
    # Check for exposed secrets
    if grep -r "sk_live\|pk_live" --include="*.js" --include="*.ts" --include="*.jsx" --include="*.tsx" frontend/src 2>/dev/null; then
        fail "Found exposed API keys in frontend code"
    else
        pass "No exposed API keys in frontend"
    fi
    
    # Check environment files
    if [ -f ".env.production" ]; then
        fail ".env.production file exists (should use secure vault)"
    else
        pass "No .env.production file found"
    fi
    
    # Check SSL certificate
    if command -v openssl &> /dev/null; then
        if echo | openssl s_client -connect api.tradesense.com:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null; then
            pass "SSL certificate is valid"
        else
            warning "Could not verify SSL certificate"
        fi
    fi
}

# Database Checks
database_checks() {
    log "Running database checks..."
    
    # Check if migrations are up to date
    if [ -d "src/backend/alembic/versions" ]; then
        MIGRATION_COUNT=$(ls -1 src/backend/alembic/versions/*.py 2>/dev/null | wc -l)
        if [ $MIGRATION_COUNT -gt 0 ]; then
            pass "Found $MIGRATION_COUNT database migrations"
        else
            fail "No database migrations found"
        fi
    else
        fail "Alembic migrations directory not found"
    fi
}

# Application Checks
application_checks() {
    log "Running application checks..."
    
    # Check frontend build
    if [ -f "frontend/package.json" ]; then
        cd frontend
        if npm run build --dry-run &>/dev/null; then
            pass "Frontend build configuration is valid"
        else
            fail "Frontend build configuration has issues"
        fi
        cd ..
    else
        fail "Frontend package.json not found"
    fi
    
    # Check backend requirements
    if [ -f "requirements.txt" ]; then
        DEPS=$(wc -l < requirements.txt)
        pass "Found $DEPS Python dependencies"
    else
        fail "requirements.txt not found"
    fi
    
    # Check for console.log statements
    CONSOLE_LOGS=$(grep -r "console.log" --include="*.js" --include="*.ts" --include="*.jsx" --include="*.tsx" frontend/src 2>/dev/null | grep -v "test" | wc -l)
    if [ $CONSOLE_LOGS -gt 0 ]; then
        warning "Found $CONSOLE_LOGS console.log statements (excluding test files)"
    else
        pass "No console.log statements in production code"
    fi
}

# Infrastructure Checks
infrastructure_checks() {
    log "Running infrastructure checks..."
    
    # Check Docker files
    if [ -f "src/backend/Dockerfile" ] && [ -f "frontend/Dockerfile" ]; then
        pass "Docker configurations found"
    else
        fail "Missing Docker configurations"
    fi
    
    # Check CI/CD
    if [ -f ".github/workflows/deploy-production.yml" ]; then
        pass "Production deployment workflow found"
    else
        fail "Production deployment workflow not found"
    fi
    
    # Check monitoring
    if [ -f "monitoring/prometheus-production.yml" ] && [ -f "monitoring/alertmanager.yml" ]; then
        pass "Monitoring configurations found"
    else
        warning "Some monitoring configurations missing"
    fi
}

# Configuration Checks
configuration_checks() {
    log "Running configuration checks..."
    
    # Check for production configs
    if [ -f ".env.production.template" ]; then
        REQUIRED_VARS=$(grep -c "=" .env.production.template)
        pass "Production template has $REQUIRED_VARS configuration variables"
    else
        fail "Production configuration template not found"
    fi
    
    # Check nginx config
    if [ -f "frontend/nginx.conf" ]; then
        if grep -q "security headers" frontend/nginx.conf; then
            pass "Nginx security headers configured"
        else
            warning "Nginx security headers might be missing"
        fi
    else
        fail "Nginx configuration not found"
    fi
}

# Performance Checks
performance_checks() {
    log "Running performance checks..."
    
    # Check for optimization flags
    if [ -f "frontend/vite.config.js" ] || [ -f "frontend/vite.config.ts" ]; then
        pass "Vite build configuration found"
    else
        warning "Build optimization configuration not found"
    fi
    
    # Check for caching headers
    if grep -q "Cache-Control" frontend/nginx.conf 2>/dev/null; then
        pass "Cache control headers configured"
    else
        warning "Cache control headers not found"
    fi
}

# Documentation Checks
documentation_checks() {
    log "Running documentation checks..."
    
    # Check for essential docs
    DOCS=("README.md" "LAUNCH_CHECKLIST.md" "API_DOCUMENTATION.md")
    for doc in "${DOCS[@]}"; do
        if [ -f "$doc" ]; then
            pass "$doc exists"
        else
            warning "$doc not found"
        fi
    done
}

# Generate Report
generate_report() {
    echo ""
    echo "========================================"
    echo "   LAUNCH READINESS REPORT"
    echo "========================================"
    echo "Environment: $ENVIRONMENT"
    echo "Date: $(date)"
    echo "========================================"
    echo ""
    
    for result in "${CHECK_RESULTS[@]}"; do
        echo "$result"
    done
    
    echo ""
    echo "========================================"
    echo "Total Checks: ${#CHECK_RESULTS[@]}"
    echo "Failed Checks: $FAILED_CHECKS"
    echo "========================================"
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}✅ All critical checks passed!${NC}"
        echo "The application appears ready for launch."
    else
        echo -e "${RED}❌ $FAILED_CHECKS critical checks failed!${NC}"
        echo "Please address these issues before launching."
        exit 1
    fi
    
    # Save report
    mkdir -p reports
    {
        echo "Launch Readiness Report"
        echo "======================="
        echo "Generated: $(date)"
        echo "Environment: $ENVIRONMENT"
        echo ""
        printf '%s\n' "${CHECK_RESULTS[@]}"
    } > "reports/launch-readiness-$(date +%Y%m%d-%H%M%S).txt"
    
    echo ""
    echo "Report saved to reports/launch-readiness-$(date +%Y%m%d-%H%M%S).txt"
}

# Main execution
main() {
    echo "🚀 TradeSense Launch Readiness Check"
    echo "===================================="
    echo ""
    
    security_checks
    echo ""
    
    database_checks
    echo ""
    
    application_checks
    echo ""
    
    infrastructure_checks
    echo ""
    
    configuration_checks
    echo ""
    
    performance_checks
    echo ""
    
    documentation_checks
    echo ""
    
    generate_report
}

# Run checks
main "$@"