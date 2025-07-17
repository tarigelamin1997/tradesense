#!/bin/bash

# TradeSense Deployment Verification Script
# Comprehensive verification of production deployment

set -e

# Configuration
ENVIRONMENT="${1:-production}"
API_URL="https://api.tradesense.com"
APP_URL="https://tradesense.com"
NAMESPACE="tradesense"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test results
PASSED=0
FAILED=0
WARNINGS=0

# Functions
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

test_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

test_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# 1. Kubernetes Resources Check
verify_kubernetes() {
    print_header "Kubernetes Resources"
    
    # Check deployments
    echo "Checking deployments..."
    for deployment in backend frontend postgres redis; do
        if kubectl get deployment $deployment -n $NAMESPACE &>/dev/null; then
            replicas=$(kubectl get deployment $deployment -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
            desired=$(kubectl get deployment $deployment -n $NAMESPACE -o jsonpath='{.spec.replicas}')
            if [ "$replicas" = "$desired" ]; then
                test_pass "$deployment deployment: $replicas/$desired replicas ready"
            else
                test_fail "$deployment deployment: $replicas/$desired replicas ready"
            fi
        else
            test_fail "$deployment deployment not found"
        fi
    done
    
    # Check pods
    echo -e "\nChecking pods..."
    unhealthy_pods=$(kubectl get pods -n $NAMESPACE -o json | jq '.items[] | select(.status.phase != "Running") | .metadata.name' | wc -l)
    if [ "$unhealthy_pods" -eq 0 ]; then
        test_pass "All pods are healthy"
    else
        test_fail "$unhealthy_pods unhealthy pods found"
        kubectl get pods -n $NAMESPACE | grep -v Running
    fi
    
    # Check services
    echo -e "\nChecking services..."
    for service in backend-service frontend-service postgres-service redis-service; do
        if kubectl get service $service -n $NAMESPACE &>/dev/null; then
            test_pass "$service exists"
        else
            test_fail "$service not found"
        fi
    done
    
    # Check ingress
    echo -e "\nChecking ingress..."
    if kubectl get ingress tradesense-ingress -n $NAMESPACE &>/dev/null; then
        test_pass "Ingress configured"
    else
        test_fail "Ingress not found"
    fi
    
    # Check secrets
    echo -e "\nChecking secrets..."
    for secret in postgres-credentials tradesense-secrets aws-credentials tradesense-tls; do
        if kubectl get secret $secret -n $NAMESPACE &>/dev/null; then
            test_pass "Secret $secret exists"
        else
            test_fail "Secret $secret not found"
        fi
    done
}

# 2. API Health Checks
verify_api() {
    print_header "API Health Checks"
    
    # Basic health check
    echo "Testing health endpoint..."
    if response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/api/v1/monitoring/health); then
        if [ "$response" = "200" ]; then
            test_pass "Health endpoint returned 200"
        else
            test_fail "Health endpoint returned $response"
        fi
    else
        test_fail "Health endpoint unreachable"
    fi
    
    # Detailed health check
    echo -e "\nTesting detailed health..."
    if health_data=$(curl -s $API_URL/api/v1/monitoring/health/detailed); then
        db_status=$(echo $health_data | jq -r '.database.status' 2>/dev/null || echo "unknown")
        cache_status=$(echo $health_data | jq -r '.cache.status' 2>/dev/null || echo "unknown")
        
        if [ "$db_status" = "healthy" ]; then
            test_pass "Database is healthy"
        else
            test_fail "Database status: $db_status"
        fi
        
        if [ "$cache_status" = "healthy" ]; then
            test_pass "Cache is healthy"
        else
            test_fail "Cache status: $cache_status"
        fi
    else
        test_fail "Detailed health check failed"
    fi
    
    # Test key endpoints
    echo -e "\nTesting API endpoints..."
    endpoints=(
        "/api/v1/auth/health"
        "/api/v1/trades"
        "/api/v1/analytics/dashboard"
        "/api/v1/journal/entries"
    )
    
    for endpoint in "${endpoints[@]}"; do
        response=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer test" $API_URL$endpoint)
        if [ "$response" = "200" ] || [ "$response" = "401" ]; then
            test_pass "$endpoint is responding"
        else
            test_fail "$endpoint returned $response"
        fi
    done
}

# 3. Frontend Verification
verify_frontend() {
    print_header "Frontend Verification"
    
    # Check main page
    echo "Testing frontend main page..."
    if response=$(curl -s -o /dev/null -w "%{http_code}" $APP_URL); then
        if [ "$response" = "200" ]; then
            test_pass "Frontend main page returned 200"
        else
            test_fail "Frontend main page returned $response"
        fi
    else
        test_fail "Frontend unreachable"
    fi
    
    # Check static assets
    echo -e "\nTesting static assets..."
    if curl -s $APP_URL | grep -q "TradeSense"; then
        test_pass "Frontend content loaded correctly"
    else
        test_fail "Frontend content missing"
    fi
    
    # Check critical paths
    paths=("/login" "/register" "/dashboard" "/analytics")
    for path in "${paths[@]}"; do
        response=$(curl -s -o /dev/null -w "%{http_code}" $APP_URL$path)
        if [ "$response" = "200" ] || [ "$response" = "302" ]; then
            test_pass "$path is accessible"
        else
            test_warn "$path returned $response"
        fi
    done
}

# 4. SSL/TLS Verification
verify_ssl() {
    print_header "SSL/TLS Verification"
    
    # Check certificate
    echo "Checking SSL certificate..."
    if openssl s_client -connect tradesense.com:443 -servername tradesense.com < /dev/null 2>/dev/null | openssl x509 -noout -dates &>/dev/null; then
        test_pass "SSL certificate is valid"
        
        # Check expiration
        expiry=$(openssl s_client -connect tradesense.com:443 -servername tradesense.com < /dev/null 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
        expiry_epoch=$(date -d "$expiry" +%s)
        current_epoch=$(date +%s)
        days_left=$(( ($expiry_epoch - $current_epoch) / 86400 ))
        
        if [ $days_left -gt 30 ]; then
            test_pass "SSL certificate expires in $days_left days"
        else
            test_warn "SSL certificate expires in $days_left days"
        fi
    else
        test_fail "SSL certificate check failed"
    fi
    
    # Check TLS version
    echo -e "\nChecking TLS version..."
    if openssl s_client -connect tradesense.com:443 -tls1_2 < /dev/null 2>/dev/null | grep -q "Protocol.*TLSv1.2"; then
        test_pass "TLS 1.2 supported"
    else
        test_fail "TLS 1.2 not supported"
    fi
}

# 5. Performance Verification
verify_performance() {
    print_header "Performance Verification"
    
    # Test response times
    echo "Testing response times..."
    for i in {1..5}; do
        response_time=$(curl -s -o /dev/null -w "%{time_total}" $API_URL/api/v1/monitoring/health)
        response_ms=$(echo "$response_time * 1000" | bc | cut -d. -f1)
        
        if [ "$response_ms" -lt 200 ]; then
            test_pass "Health check response time: ${response_ms}ms"
        elif [ "$response_ms" -lt 500 ]; then
            test_warn "Health check response time: ${response_ms}ms (slow)"
        else
            test_fail "Health check response time: ${response_ms}ms (too slow)"
        fi
        
        sleep 1
    done
    
    # Check concurrent connections
    echo -e "\nTesting concurrent connections..."
    (for i in {1..10}; do curl -s $API_URL/api/v1/monitoring/health & done; wait) 2>/dev/null
    if [ $? -eq 0 ]; then
        test_pass "Handled 10 concurrent requests"
    else
        test_fail "Failed handling concurrent requests"
    fi
}

# 6. Database Verification
verify_database() {
    print_header "Database Verification"
    
    # Check database connection
    echo "Checking database connection..."
    if kubectl exec deployment/backend -n $NAMESPACE -- python -c "from app.core.db.session import engine; print(engine.execute('SELECT 1').scalar())" &>/dev/null; then
        test_pass "Database connection successful"
    else
        test_fail "Database connection failed"
    fi
    
    # Check database size
    echo -e "\nChecking database metrics..."
    db_size=$(kubectl exec deployment/postgres -n $NAMESPACE -- psql -U tradesense -d tradesense -t -c "SELECT pg_size_pretty(pg_database_size('tradesense'));" | xargs)
    test_pass "Database size: $db_size"
    
    # Check connection count
    conn_count=$(kubectl exec deployment/postgres -n $NAMESPACE -- psql -U tradesense -d tradesense -t -c "SELECT count(*) FROM pg_stat_activity;" | xargs)
    if [ "$conn_count" -lt 50 ]; then
        test_pass "Database connections: $conn_count"
    else
        test_warn "High database connections: $conn_count"
    fi
}

# 7. Monitoring Verification
verify_monitoring() {
    print_header "Monitoring Verification"
    
    # Check metrics endpoint
    echo "Checking metrics endpoint..."
    if curl -s $API_URL/metrics | grep -q "tradesense_http_requests_total"; then
        test_pass "Metrics endpoint is working"
    else
        test_fail "Metrics endpoint not working"
    fi
    
    # Check Prometheus
    echo -e "\nChecking Prometheus..."
    if kubectl get deployment prometheus-server -n monitoring &>/dev/null; then
        test_pass "Prometheus is running"
    else
        test_warn "Prometheus not found"
    fi
    
    # Check Grafana
    echo -e "\nChecking Grafana..."
    if kubectl get deployment grafana -n monitoring &>/dev/null; then
        test_pass "Grafana is running"
    else
        test_warn "Grafana not found"
    fi
}

# 8. Backup Verification
verify_backups() {
    print_header "Backup Verification"
    
    # Check backup CronJobs
    echo "Checking backup jobs..."
    for job in postgres-backup redis-backup files-backup; do
        if kubectl get cronjob $job -n $NAMESPACE &>/dev/null; then
            schedule=$(kubectl get cronjob $job -n $NAMESPACE -o jsonpath='{.spec.schedule}')
            test_pass "$job scheduled: $schedule"
        else
            test_fail "$job not found"
        fi
    done
    
    # Check last backup
    echo -e "\nChecking recent backups..."
    last_backup=$(kubectl get jobs -n $NAMESPACE -l job-type=backup --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1:].metadata.name}')
    if [ -n "$last_backup" ]; then
        test_pass "Last backup job: $last_backup"
    else
        test_warn "No recent backup jobs found"
    fi
}

# 9. Security Verification
verify_security() {
    print_header "Security Verification"
    
    # Check security headers
    echo "Checking security headers..."
    headers=$(curl -s -I $APP_URL)
    
    security_headers=(
        "Strict-Transport-Security"
        "X-Frame-Options"
        "X-Content-Type-Options"
        "X-XSS-Protection"
        "Referrer-Policy"
    )
    
    for header in "${security_headers[@]}"; do
        if echo "$headers" | grep -qi "$header"; then
            test_pass "$header header present"
        else
            test_fail "$header header missing"
        fi
    done
    
    # Check rate limiting
    echo -e "\nChecking rate limiting..."
    for i in {1..10}; do
        curl -s -o /dev/null $API_URL/api/v1/monitoring/health
    done
    
    response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/api/v1/monitoring/health)
    if [ "$response" = "429" ]; then
        test_pass "Rate limiting is working"
    else
        test_warn "Rate limiting may not be configured properly"
    fi
}

# 10. Final Summary
print_summary() {
    print_header "Deployment Verification Summary"
    
    echo "Total Tests: $((PASSED + FAILED + WARNINGS))"
    echo -e "${GREEN}Passed: $PASSED${NC}"
    echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
    echo -e "${RED}Failed: $FAILED${NC}"
    
    if [ $FAILED -eq 0 ]; then
        echo -e "\n${GREEN}✓ Deployment verification PASSED!${NC}"
        echo "TradeSense is successfully deployed to $ENVIRONMENT"
        exit 0
    else
        echo -e "\n${RED}✗ Deployment verification FAILED!${NC}"
        echo "Please review the failed tests above"
        exit 1
    fi
}

# Main execution
main() {
    echo "========================================="
    echo "TradeSense Deployment Verification"
    echo "========================================="
    echo "Environment: $ENVIRONMENT"
    echo "API URL: $API_URL"
    echo "App URL: $APP_URL"
    echo "Time: $(date)"
    echo ""
    
    verify_kubernetes
    verify_api
    verify_frontend
    verify_ssl
    verify_performance
    verify_database
    verify_monitoring
    verify_backups
    verify_security
    
    print_summary
}

# Run verification
main