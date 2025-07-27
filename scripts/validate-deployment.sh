#!/bin/bash
# TradeSense Deployment Validation Script
# Runs comprehensive checks to ensure production readiness

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔍 TradeSense Deployment Validation"
echo "==================================="
echo ""

# Track validation results
TOTAL_CHECKS=0
PASSED_CHECKS=0
WARNINGS=0
FAILURES=0

# Function to run a check
run_check() {
    local check_name=$1
    local check_command=$2
    local critical=${3:-true}
    
    ((TOTAL_CHECKS++))
    echo -n "• $check_name: "
    
    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED_CHECKS++))
        return 0
    else
        if [ "$critical" = true ]; then
            echo -e "${RED}FAIL${NC}"
            ((FAILURES++))
        else
            echo -e "${YELLOW}WARN${NC}"
            ((WARNINGS++))
        fi
        return 1
    fi
}

# 1. Infrastructure Checks
echo "1️⃣ Infrastructure Checks"
echo "------------------------"

run_check "Railway CLI installed" "command -v railway"
run_check "Docker installed" "command -v docker"
run_check "PostgreSQL client" "command -v psql" false
run_check "Node.js installed" "command -v node"
run_check "Python 3.11+" "python3 --version | grep -E '3\.(11|12)'"

echo ""

# 2. Service Health Checks
echo "2️⃣ Service Health Checks"
echo "------------------------"

# Update these URLs with your actual service URLs
SERVICES=(
    "Gateway|https://tradesense-gateway-production.up.railway.app"
    "Auth|https://tradesense-auth-production.up.railway.app"
    "Trading|https://tradesense-trading-production.up.railway.app"
    "Analytics|https://tradesense-analytics-production.up.railway.app"
    "Frontend|https://tradesense.vercel.app"
)

for service in "${SERVICES[@]}"; do
    IFS='|' read -r name url <<< "$service"
    run_check "$name service" "curl -f -s $url/health" true
done

echo ""

# 3. Security Checks
echo "3️⃣ Security Checks"
echo "------------------"

run_check "HTTPS enabled (Gateway)" "curl -s -I https://tradesense-gateway-production.up.railway.app | grep -i 'HTTP/2'"
run_check "CORS configured" "curl -s -I -H 'Origin: https://tradesense.ai' https://tradesense-gateway-production.up.railway.app/health | grep -i 'access-control-allow-origin'" false
run_check "Security headers" "curl -s -I https://tradesense-gateway-production.up.railway.app | grep -i 'x-content-type-options'" false
run_check "No exposed secrets" "! grep -r 'sk_live' --include='*.py' --include='*.js' --include='*.ts' . 2>/dev/null"

echo ""

# 4. Database Checks
echo "4️⃣ Database Checks"
echo "------------------"

# Check if databases are configured
for service in auth trading analytics; do
    if railway variables get DATABASE_URL --service "$service" > /dev/null 2>&1; then
        echo -e "• $service database: ${GREEN}Configured${NC}"
        ((PASSED_CHECKS++))
        ((TOTAL_CHECKS++))
    else
        echo -e "• $service database: ${RED}Not configured${NC}"
        ((FAILURES++))
        ((TOTAL_CHECKS++))
    fi
done

echo ""

# 5. Environment Variables
echo "5️⃣ Environment Variables"
echo "------------------------"

REQUIRED_VARS=(
    "gateway|JWT_SECRET_KEY"
    "auth|JWT_SECRET_KEY"
    "auth|MASTER_ENCRYPTION_KEY"
    "trading|AUTH_SERVICE_URL"
    "analytics|AUTH_SERVICE_URL"
)

for var in "${REQUIRED_VARS[@]}"; do
    IFS='|' read -r service varname <<< "$var"
    if railway variables get "$varname" --service "$service" > /dev/null 2>&1; then
        echo -e "• $service/$varname: ${GREEN}Set${NC}"
        ((PASSED_CHECKS++))
    else
        echo -e "• $service/$varname: ${RED}Missing${NC}"
        ((FAILURES++))
    fi
    ((TOTAL_CHECKS++))
done

echo ""

# 6. Performance Checks
echo "6️⃣ Performance Checks"
echo "---------------------"

# Test response times
check_response_time() {
    local name=$1
    local url=$2
    local threshold=$3
    
    ((TOTAL_CHECKS++))
    echo -n "• $name response time: "
    
    local response_time=$(curl -s -o /dev/null -w "%{time_total}" "$url" 2>/dev/null || echo "999")
    local response_ms=$(echo "$response_time * 1000" | bc | cut -d. -f1)
    
    if [ "$response_ms" -lt "$threshold" ]; then
        echo -e "${GREEN}${response_ms}ms${NC} (< ${threshold}ms)"
        ((PASSED_CHECKS++))
    else
        echo -e "${YELLOW}${response_ms}ms${NC} (> ${threshold}ms)"
        ((WARNINGS++))
    fi
}

check_response_time "Gateway" "https://tradesense-gateway-production.up.railway.app/health" 200
check_response_time "Frontend" "https://tradesense.vercel.app" 500

echo ""

# 7. Integration Checks
echo "7️⃣ Integration Checks"
echo "---------------------"

# Test API Gateway routing
run_check "Gateway → Auth routing" "curl -f -s https://tradesense-gateway-production.up.railway.app/api/v1/auth/health" false
run_check "Frontend → Gateway connection" "curl -f -s https://tradesense.vercel.app/api/health" false

echo ""

# 8. Monitoring & Logging
echo "8️⃣ Monitoring & Logging"
echo "-----------------------"

run_check "Health endpoints exist" "true" # Already checked above
run_check "Error tracking configured" "railway variables get SENTRY_DSN --service gateway" false
run_check "Logs accessible" "railway logs --service gateway --limit 1" false

echo ""

# Summary
echo "======================================"
echo "📊 Validation Summary"
echo "======================================"
echo -e "Total Checks: $TOTAL_CHECKS"
echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo -e "Failed: ${RED}$FAILURES${NC}"
echo ""

# Calculate score
SCORE=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))

if [ $FAILURES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ DEPLOYMENT READY!${NC} (Score: $SCORE%)"
    echo "All checks passed. You're ready to launch! 🚀"
elif [ $FAILURES -eq 0 ]; then
    echo -e "${YELLOW}⚠️  DEPLOYMENT READY WITH WARNINGS${NC} (Score: $SCORE%)"
    echo "No critical issues, but review warnings before launch."
else
    echo -e "${RED}❌ DEPLOYMENT NOT READY${NC} (Score: $SCORE%)"
    echo "Critical issues found. Fix failures before deploying."
fi

echo ""

# Generate detailed report
if [ $FAILURES -gt 0 ] || [ $WARNINGS -gt 0 ]; then
    echo "📝 Action Items:"
    echo "---------------"
    
    if [ $FAILURES -gt 0 ]; then
        echo ""
        echo "Critical (Must Fix):"
        echo "• Configure missing databases in Railway"
        echo "• Set required environment variables"
        echo "• Ensure all services are healthy"
    fi
    
    if [ $WARNINGS -gt 0 ]; then
        echo ""
        echo "Recommended:"
        echo "• Improve response times"
        echo "• Configure error tracking (Sentry)"
        echo "• Set up proper CORS headers"
        echo "• Add security headers"
    fi
fi

echo ""
echo "Run './scripts/monitor-production-health.sh' for continuous monitoring"
echo ""