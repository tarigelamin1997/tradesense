#!/bin/bash

# TradeSense Pre-commit Hook
# Automatically checks for protected file modifications and code quality

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Running pre-commit checks...${NC}"

# 1. Check protected files
protected_files=$(git diff --cached --name-only | grep -E "(COMPLETE_SAAS_ARCHITECTURE_GUIDE/|PROTECTED_FILES\.md|project-rules\.md|README\.md|README_DEV\.md)")

if [ ! -z "$protected_files" ]; then
    echo -e "${YELLOW}⚠️  Warning: Protected files modified:${NC}"
    echo "$protected_files"
    echo ""
    echo "Please ensure you have approval to modify these files."
    echo "Add a comment in your commit message explaining the changes."
fi

# 2. Check for merge conflict markers
if git diff --cached --name-only | xargs grep -H "<<<<<<< HEAD" 2>/dev/null; then
    echo -e "${RED}✗ Merge conflict markers found!${NC}"
    exit 1
fi

# 3. Check Python files for syntax errors
python_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)
if [ ! -z "$python_files" ]; then
    for file in $python_files; do
        if ! python -m py_compile "$file" 2>/dev/null; then
            echo -e "${RED}✗ Python syntax error in: $file${NC}"
            exit 1
        fi
    done
    echo -e "${GREEN}✓ Python syntax check passed${NC}"
fi

# 4. Check for sensitive data
if git diff --cached --name-only | xargs grep -E "(password|secret|api_key|private_key)[\s]*=[\s]*[\"'][^\"']+[\"']" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Possible sensitive data detected!${NC}"
    echo "Please review your changes for hardcoded credentials."
    read -p "Continue anyway? (yes/no): " response
    if [ "$response" != "yes" ]; then
        exit 1
    fi
fi

# 5. Check file size
large_files=$(git diff --cached --name-only | xargs -I {} find {} -size +5M 2>/dev/null)
if [ ! -z "$large_files" ]; then
    echo -e "${YELLOW}⚠️  Large files detected (>5MB):${NC}"
    echo "$large_files"
    echo "Consider using Git LFS for large files."
fi

echo -e "${GREEN}✓ Pre-commit checks completed${NC}"
exit 0
