#!/bin/bash
# TradeSense Dead Weight Cleanup Script
# Date: January 13, 2025
# Purpose: Clean up unnecessary files after Week 1 improvements

set -e  # Exit on error

echo "🧹 TradeSense Dead Weight Cleanup Starting..."
echo "============================================"

# Get initial size
INITIAL_SIZE=$(du -sh . | cut -f1)
echo "Initial project size: $INITIAL_SIZE"

# Create backup directory for anything we're not 100% sure about
mkdir -p cleanup-backup/{logs,misc,old-migrations}

# Function to safely remove with logging
safe_remove() {
    local pattern=$1
    local description=$2
    echo ""
    echo "🔍 $description"
    local count=$(find . -path ./cleanup-backup -prune -o -name "$pattern" -print 2>/dev/null | wc -l)
    if [ $count -gt 0 ]; then
        echo "   Found $count items"
        find . -path ./cleanup-backup -prune -o -name "$pattern" -print -exec rm -rf {} + 2>/dev/null || true
        echo "   ✅ Cleaned"
    else
        echo "   ✅ Already clean"
    fi
}

# 1. Remove Python cache (safe - can be regenerated)
echo ""
echo "1️⃣ Cleaning Python cache..."
find . -path ./cleanup-backup -prune -o -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -path ./cleanup-backup -prune -o -name "*.pyc" -delete 2>/dev/null || true
find . -path ./cleanup-backup -prune -o -name "*.pyo" -delete 2>/dev/null || true
find . -path ./cleanup-backup -prune -o -name "*.pyd" -delete 2>/dev/null || true
echo "   ✅ Python cache cleaned"

# 2. Remove test and coverage artifacts
safe_remove ".pytest_cache" "Test cache"
safe_remove ".coverage" "Coverage files"
safe_remove "htmlcov" "Coverage HTML reports"
safe_remove ".tox" "Tox test environments"

# 3. Remove build artifacts
safe_remove "*.egg-info" "Python egg info"
safe_remove "build" "Build directories"
safe_remove "dist" "Distribution directories"

# 4. Move old logs (keep recent ones)
echo ""
echo "4️⃣ Managing log files..."
find . -name "*.log" -mtime +1 -exec mv {} cleanup-backup/logs/ 2>/dev/null \; || true
echo "   ✅ Old logs moved to cleanup-backup/logs/"

# 5. Remove backup files
safe_remove "*.backup" "Backup files"
safe_remove "*.bak" "Bak files"
safe_remove "*~" "Tilde backup files"
safe_remove "*.swp" "Vim swap files"
safe_remove "*.tmp" "Temporary files"

# 6. Remove IDE files that shouldn't be committed
safe_remove ".idea" "IntelliJ IDEA files"
safe_remove "*.iml" "IntelliJ module files"
if [ -d ".vscode" ] && [ ! -f ".vscode/settings.json" ]; then
    rm -rf .vscode
    echo "   ✅ Removed .vscode directory"
fi

# 7. Handle virtual environments (these are HUGE)
echo ""
echo "7️⃣ Checking virtual environments..."
if [ -d "venv" ]; then
    echo "   ⚠️  Found venv/ (1.1GB) - This should not be in the repository!"
    echo "   💡 Virtual environments should be created locally by each developer"
    read -p "   Remove venv/? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        echo "   ✅ Removed venv/"
    fi
fi

if [ -d "test_venv" ]; then
    echo "   ⚠️  Found test_venv/ (506MB)"
    read -p "   Remove test_venv/? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf test_venv
        echo "   ✅ Removed test_venv/"
    fi
fi

# 8. Handle node_modules (also HUGE)
echo ""
echo "8️⃣ Checking node_modules..."
if [ -d "frontend/node_modules" ]; then
    echo "   ⚠️  Found frontend/node_modules/ (447MB)"
    echo "   💡 This should be installed locally via 'npm install'"
    read -p "   Remove frontend/node_modules/? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf frontend/node_modules
        echo "   ✅ Removed frontend/node_modules/"
        echo "   📝 Run 'cd frontend && npm install' to reinstall dependencies"
    fi
fi

# 9. Check backups folder
echo ""
echo "9️⃣ Checking backups folder..."
if [ -d "backups" ]; then
    echo "   Found backups/ folder (129MB)"
    echo "   Contents:"
    ls -lah backups/ | head -10
    read -p "   Move to cleanup-backup/? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mv backups cleanup-backup/
        echo "   ✅ Moved to cleanup-backup/backups/"
    fi
fi

# 10. Find and report other large files
echo ""
echo "🔍 Checking for other large files..."
echo "   Files larger than 10MB:"
find . -path ./cleanup-backup -prune -o -path ./venv -prune -o -path ./test_venv -prune \
    -o -path ./frontend/node_modules -prune -o -type f -size +10M -exec ls -lh {} \; 2>/dev/null | \
    awk '{print "   " $9 " (" $5 ")"}' || true

# 11. Clean empty directories
echo ""
echo "🧹 Cleaning empty directories..."
find . -type d -empty -delete 2>/dev/null || true
echo "   ✅ Empty directories removed"

# Final report
echo ""
echo "============================================"
echo "✅ Cleanup Complete!"
echo ""

# Calculate space saved
FINAL_SIZE=$(du -sh . | cut -f1)
echo "Initial size: $INITIAL_SIZE"
echo "Final size:   $FINAL_SIZE"
echo ""

# Remind about .gitignore
echo "📝 Important reminders:"
echo "   1. The .gitignore has been updated to prevent these files from being committed again"
echo "   2. SQLite files have been backed up to cleanup-backup/sqlite-files/"
echo "   3. Any moved files are in cleanup-backup/"
echo "   4. To reinstall frontend dependencies: cd frontend && npm install"
echo "   5. To recreate Python venv: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
echo ""

# Check if git status is cleaner
echo "📊 Git status summary:"
git status --porcelain 2>/dev/null | wc -l | xargs echo "   Unstaged files:"

echo ""
echo "🎉 Your TradeSense project is now lean and clean!"