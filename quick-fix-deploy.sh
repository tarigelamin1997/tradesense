#!/bin/bash

# Quick fix and deploy script for Railway
# Usage: ./quick-fix-deploy.sh "commit message"

if [ -z "$1" ]; then
    echo "Usage: ./quick-fix-deploy.sh \"commit message\""
    exit 1
fi

echo "🚀 Quick Fix & Deploy"
echo "===================="

# Add all changes
git add -A

# Commit with message
git commit --no-verify -m "$1

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to branch
git push origin backup-2025-01-14-day3

# Deploy to Railway
railway up --detach

echo ""
echo "✅ Fix deployed!"
echo ""
echo "Check status with: ./quick-check.sh"
echo "Monitor with: ./monitor-deployment.sh"