#!/bin/bash

# Validation script for repository restructuring
# Run this after restructuring to ensure everything is correct

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔍 Validating Repository Structure..."

# Check protected files
echo -e "\n📁 Checking Protected Files:"

protected_files=(
    "docs/architecture/COMPLETE_SAAS_ARCHITECTURE_GUIDE/ARCHITECTURE_STRATEGY.md"
    "docs/project/PROTECTED_FILES.md"
    "docs/project/project-rules.md"
    "README.md"
    "README_DEV.md"
)

for file in "${protected_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file exists${NC}"
    else
        echo -e "${RED}✗ $file missing!${NC}"
        exit 1
    fi
done

# Check directory structure
echo -e "\n📂 Checking Directory Structure:"

directories=(
    ".github/workflows"
    ".github/ISSUE_TEMPLATE"
    "docs/architecture"
    "docs/api"
    "docs/guides"
    "docs/project"
    "src/app"
    "src/services"
    "src/models"
    "tests"
    "scripts"
    "config"
)

for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓ $dir exists${NC}"
    else
        echo -e "${RED}✗ $dir missing!${NC}"
    fi
done

# Check moved files
echo -e "\n📄 Checking Moved Files:"

moved_files=(
    "scripts/git-workflow.sh"
    "docs/guides/GIT_WORKFLOW_GUIDE.md"
    "docs/guides/GIT_QUICK_REFERENCE.md"
)

for file in "${moved_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file in new location${NC}"
    else
        echo -e "${RED}✗ $file not found in expected location${NC}"
    fi
done

# Check Python imports
echo -e "\n🐍 Checking Python Installation:"
if python -c "from src.app import *" 2>/dev/null; then
    echo -e "${GREEN}✓ Python imports working${NC}"
else
    echo -e "${RED}✗ Python imports need updating${NC}"
fi

echo -e "\n✅ Validation Complete!"
