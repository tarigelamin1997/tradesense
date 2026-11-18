#!/bin/bash

# Railway Pre-Deployment Validation Script
# This script checks for common issues before deploying to Railway

set -e

echo "🔍 Railway Pre-Deployment Validation"
echo "===================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to report errors
error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    ((ERRORS++))
}

# Function to report warnings
warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    ((WARNINGS++))
}

# Function to report success
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 1. Check Python syntax
echo -e "\n📝 Checking Python syntax..."
if python3 -m py_compile src/backend/main.py 2>/dev/null; then
    success "Python syntax is valid"
else
    error "Python syntax errors found in main.py"
fi

# 2. Check for import errors
echo -e "\n📦 Checking imports..."
cd src/backend
if python3 -c "import main" 2>/dev/null; then
    success "All imports successful"
else
    error "Import errors detected - check the error messages above"
fi
cd ../..

# 3. Check required environment variables
echo -e "\n🔐 Checking environment variables..."
REQUIRED_VARS=(
    "DATABASE_URL"
    "SECRET_KEY"
    "JWT_SECRET_KEY"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        warning "$var is not set (will need to be set in Railway)"
    else
        success "$var is set"
    fi
done

# 4. Check Dockerfile
echo -e "\n🐳 Checking Dockerfile..."
if [ -f "src/backend/Dockerfile" ]; then
    success "Dockerfile found"
    
    # Check for development flags
    if grep -q "\-\-reload" src/backend/Dockerfile; then
        error "Dockerfile contains --reload flag (not suitable for production)"
    fi
    
    # Check for proper port handling
    if grep -q "PORT" src/backend/Dockerfile; then
        success "Dockerfile handles PORT environment variable"
    else
        warning "Dockerfile doesn't reference PORT variable"
    fi
else
    error "Dockerfile not found at src/backend/Dockerfile"
fi

# 5. Check railway.toml configuration
echo -e "\n🚂 Checking Railway configuration..."
if [ -f "railway.toml" ]; then
    success "railway.toml found"
    
    # Basic validation of TOML syntax
    if python3 -c "import toml; toml.load('railway.toml')" 2>/dev/null; then
        success "railway.toml syntax is valid"
    else
        warning "Could not validate railway.toml syntax (toml module not installed)"
    fi
else
    warning "railway.toml not found (using defaults)"
fi

# 6. Check for common issues in code
echo -e "\n🔎 Checking for common deployment issues..."

# Check for hardcoded localhost URLs
if grep -r "localhost" src/backend --include="*.py" | grep -v "__pycache__" | grep -v ".pyc"; then
    warning "Found hardcoded localhost references - ensure these are configurable"
fi

# Check for missing __init__.py files
find src/backend -type d -name "*" ! -path "*/\.*" ! -path "*/__pycache__*" | while read dir; do
    if [ ! -f "$dir/__init__.py" ]; then
        warning "Missing __init__.py in $dir"
    fi
done

# 7. Check database migrations
echo -e "\n🗄️  Checking database setup..."
if [ -f "src/backend/alembic.ini" ]; then
    success "Alembic configuration found"
else
    warning "No alembic.ini found - database migrations may not be configured"
fi

# 8. Summary
echo -e "\n📊 Validation Summary"
echo "===================="
echo -e "Errors: ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"

if [ $ERRORS -eq 0 ]; then
    echo -e "\n${GREEN}✅ Ready for deployment!${NC}"
    echo -e "\nNext steps:"
    echo "1. Commit all changes: git add . && git commit -m 'Your message'"
    echo "2. Push to GitHub: git push origin backup-2025-01-14-day3"
    echo "3. Deploy to Railway: railway up --detach"
    exit 0
else
    echo -e "\n${RED}❌ Fix errors before deploying!${NC}"
    exit 1
fi