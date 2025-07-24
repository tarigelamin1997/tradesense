#!/bin/bash

# TradeSense Repository Structure Verification Script
# This script verifies the repository structure is correct for CI/CD

set -e

echo "🔍 TradeSense Repository Structure Verification"
echo "============================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
ERRORS=0
WARNINGS=0

# Function to print colored output
print_check() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((ERRORS++))
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++))
}

# Check 1: No nested .git directories
print_check "Checking for nested .git directories..."
NESTED_GIT=$(find services -name ".git" -type d 2>/dev/null || true)
if [ -z "$NESTED_GIT" ]; then
    print_pass "No nested .git directories found"
else
    print_fail "Found nested .git directories:"
    echo "$NESTED_GIT"
fi

# Check 2: All services directories exist
print_check "Checking service directories..."
EXPECTED_SERVICES=("gateway" "auth" "trading" "analytics" "market-data" "billing" "ai")
for service in "${EXPECTED_SERVICES[@]}"; do
    if [ -d "services/$service" ]; then
        print_pass "Service directory exists: $service"
    else
        print_fail "Service directory missing: $service"
    fi
done

# Check 3: All services have required files
print_check "Checking service structure..."
for service in "${EXPECTED_SERVICES[@]}"; do
    if [ -d "services/$service" ]; then
        # Check for Dockerfile
        if [ -f "services/$service/Dockerfile" ]; then
            print_pass "$service has Dockerfile"
        else
            print_fail "$service missing Dockerfile"
        fi
        
        # Check for source directory
        if [ -d "services/$service/src" ]; then
            print_pass "$service has src directory"
        else
            print_fail "$service missing src directory"
        fi
        
        # Check for main.py (Python services)
        if [ -f "services/$service/src/main.py" ]; then
            print_pass "$service has main.py"
        else
            print_warning "$service missing main.py (might not be a Python service)"
        fi
    fi
done

# Check 4: Git tracking status
print_check "Checking git tracking status..."
UNTRACKED=$(git ls-files --others --exclude-standard services/ | wc -l)
if [ "$UNTRACKED" -eq 0 ]; then
    print_pass "All service files are tracked by git"
else
    print_warning "Found $UNTRACKED untracked files in services/"
    echo "Run 'git status services/' to see untracked files"
fi

# Check 5: GitHub Actions workflow
print_check "Checking GitHub Actions workflow..."
if [ -f ".github/workflows/railway-deploy.yml" ]; then
    print_pass "Railway deployment workflow exists"
    
    # Check if workflow has submodule references
    if grep -q "submodules:" ".github/workflows/railway-deploy.yml"; then
        print_warning "Workflow still contains submodule references - these should be removed"
    else
        print_pass "Workflow does not contain submodule references"
    fi
else
    print_fail "Railway deployment workflow missing"
fi

# Check 6: Service health endpoints
print_check "Checking service configurations..."
for service in "${EXPECTED_SERVICES[@]}"; do
    if [ -f "services/$service/src/main.py" ]; then
        if grep -q "/health" "services/$service/src/main.py"; then
            print_pass "$service has health endpoint"
        else
            print_warning "$service might be missing health endpoint"
        fi
    fi
done

# Check 7: Environment files
print_check "Checking environment configuration..."
if [ -f ".env.example" ]; then
    print_pass "Environment example file exists"
else
    print_warning "Missing .env.example file"
fi

# Check 8: Verify no .gitmodules file
print_check "Checking for .gitmodules..."
if [ ! -f ".gitmodules" ]; then
    print_pass "No .gitmodules file (correct for flattened structure)"
else
    print_fail ".gitmodules file exists - should be removed for flattened structure"
fi

# Summary
echo ""
echo "============================================="
echo "Verification Summary"
echo "============================================="
echo -e "Errors:   ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Repository structure is correct for CI/CD!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Commit any changes: git add . && git commit -m 'Fix repository structure'"
    echo "2. Push to trigger CI/CD: git push origin main"
    echo "3. Monitor the deployment pipeline"
    exit 0
else
    echo -e "${RED}❌ Repository structure has issues that need to be fixed${NC}"
    echo ""
    echo "Run the fix script: ./scripts/fix-repository-structure.sh"
    exit 1
fi