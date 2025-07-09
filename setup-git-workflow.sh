#!/bin/bash

# Setup script for TradeSense Git Workflow System

echo "🚀 Setting up TradeSense Git Workflow System..."

# 1. Make git-workflow.sh executable
if [ -f "git-workflow.sh" ]; then
    chmod +x git-workflow.sh
    echo "✓ Made git-workflow.sh executable"
else
    echo "✗ git-workflow.sh not found!"
    exit 1
fi

# 2. Create .git/hooks directory if it doesn't exist
mkdir -p .git/hooks

# 3. Install pre-commit hook
if [ -f ".git/hooks/pre-commit" ]; then
    echo "⚠️  Pre-commit hook already exists. Backing up..."
    mv .git/hooks/pre-commit .git/hooks/pre-commit.backup
fi

# Create the pre-commit hook content
cat > .git/hooks/pre-commit << 'EOF'
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
EOF

chmod +x .git/hooks/pre-commit
echo "✓ Installed pre-commit hook"

# 4. Create CHANGELOG.md if it doesn't exist
if [ ! -f "CHANGELOG.md" ]; then
    cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup

EOF
    echo "✓ Created CHANGELOG.md"
else
    echo "✓ CHANGELOG.md already exists"
fi

# 5. Create .gitignore entries
if ! grep -q "# Git workflow backups" .gitignore 2>/dev/null; then
    echo "" >> .gitignore
    echo "# Git workflow backups" >> .gitignore
    echo "*.backup" >> .gitignore
    echo "backup-*" >> .gitignore
    echo "✓ Updated .gitignore"
fi

# 6. Configure git aliases (optional)
read -p "Would you like to install helpful git aliases? (yes/no): " install_aliases
if [ "$install_aliases" == "yes" ]; then
    git config alias.st "status --short"
    git config alias.cm "commit -m"
    git config alias.co "checkout"
    git config alias.br "branch"
    git config alias.lg "log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"
    git config alias.last "log -1 HEAD --stat"
    git config alias.undo "reset HEAD~1 --mixed"
    git config alias.protected "!git status --short | grep -E 'COMPLETE_SAAS_ARCHITECTURE_GUIDE/|PROTECTED_FILES.md|project-rules.md'"
    echo "✓ Installed git aliases"
fi

# 7. Set up initial version tag if none exists
if ! git describe --tags >/dev/null 2>&1; then
    read -p "No version tags found. Create initial v0.1.0 tag? (yes/no): " create_initial
    if [ "$create_initial" == "yes" ]; then
        git tag -a v0.1.0 -m "Initial version"
        echo "✓ Created initial version tag v0.1.0"
    fi
fi

echo ""
echo "✅ Git Workflow System setup complete!"
echo ""
echo "Usage:"
echo "  ./git-workflow.sh     - Run the workflow system"
echo "  git st               - Short status (if aliases installed)"
echo "  git lg               - Pretty log view (if aliases installed)"
echo "  git protected        - Show protected files status"
echo ""
echo "📖 See GIT_WORKFLOW_GUIDE.md for complete documentation"
