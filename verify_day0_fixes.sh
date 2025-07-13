#!/bin/bash

# Day 0 Critical Blockers Verification Script
# Tests all 5 critical fixes

echo "🔍 Verifying Day 0 Critical Fixes..."
echo "====================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a fix is successful
check_fix() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        return 0
    else
        echo -e "${RED}❌ $2${NC}"
        return 1
    fi
}

# Counter for passed tests
PASSED=0
TOTAL=5

echo ""
echo "1️⃣ Checking Frontend API URL Configuration..."
if grep -q "import.meta.env.VITE_API_URL" frontend/src/services/api.ts && \
   [ -f "frontend/.env" ] && \
   grep -q "VITE_API_URL=http://localhost:8000" frontend/.env; then
    check_fix 0 "Frontend API URL properly configured"
    ((PASSED++))
else
    check_fix 1 "Frontend API URL configuration"
fi

echo ""
echo "2️⃣ Checking JWT Secret Configuration..."
if grep -q "os.getenv(\"JWT_SECRET_KEY\"" src/backend/core/config.py && \
   [ -f "src/backend/.env" ] && \
   grep -q "JWT_SECRET_KEY=" src/backend/.env && \
   ! grep -q "JWT_SECRET_KEY=your-secret-key-here" src/backend/.env; then
    check_fix 0 "JWT secrets secured with environment variables"
    ((PASSED++))
else
    check_fix 1 "JWT secret configuration"
fi

echo ""
echo "3️⃣ Checking CORS Configuration..."
if grep -q "settings.cors_origins" src/backend/main.py && \
   ! grep -q 'allow_origins=.*"\*"' src/backend/main.py; then
    check_fix 0 "CORS properly configured without wildcards"
    ((PASSED++))
else
    check_fix 1 "CORS configuration"
fi

echo ""
echo "4️⃣ Checking Database Connection Pooling..."
if grep -q "pool_size=20" src/backend/core/db/session.py && \
   grep -q "pool_pre_ping=True" src/backend/core/db/session.py; then
    check_fix 0 "Database connection pooling configured"
    ((PASSED++))
else
    check_fix 1 "Database connection pooling"
fi

echo ""
echo "5️⃣ Checking Test Infrastructure..."
if [ -f "src/backend/core/config_test.py" ] && \
   grep -q "postgresql://.*tradesense_test" src/backend/conftest.py && \
   [ -f "src/backend/pytest.ini" ]; then
    check_fix 0 "Test infrastructure configured"
    ((PASSED++))
else
    check_fix 1 "Test infrastructure"
fi

echo ""
echo "====================================="
echo -e "Summary: ${GREEN}$PASSED${NC}/${TOTAL} fixes verified"

if [ $PASSED -eq $TOTAL ]; then
    echo -e "${GREEN}🎉 All Day 0 blockers have been fixed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start the backend: cd src/backend && python main.py"
    echo "2. Start the frontend: cd frontend && npm run dev"
    echo "3. Test login at http://localhost:5173"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some fixes still need attention${NC}"
    exit 1
fi