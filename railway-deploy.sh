#!/bin/bash

# Railway Quick Deploy Script
# Automates the deployment process with validation

set -e

echo "🚀 Railway Quick Deploy"
echo "======================"

# Check if we're in the right directory
if [ ! -f "src/backend/main.py" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Run validation first
echo -e "\n📋 Running pre-deployment validation..."
if ./railway-validate.sh; then
    echo -e "\n✅ Validation passed!"
else
    echo -e "\n❌ Validation failed - fix errors before deploying"
    exit 1
fi

# Check for uncommitted changes
echo -e "\n📝 Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  You have uncommitted changes:"
    git status --short
    
    read -p "Do you want to commit these changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter commit message: " commit_msg
        git add .
        git commit -m "$commit_msg" --no-verify
    else
        echo "⚠️  Deploying with uncommitted changes..."
    fi
fi

# Push to GitHub
echo -e "\n📤 Pushing to GitHub..."
current_branch=$(git branch --show-current)
git push origin $current_branch

# Deploy to Railway
echo -e "\n🚂 Deploying to Railway..."
railway up --detach

echo -e "\n✅ Deployment initiated!"
echo "Monitor progress at: https://railway.app/dashboard"
echo ""
echo "Next steps:"
echo "1. Check Railway dashboard for deployment status"
echo "2. Run ./railway-status.sh to check health"
echo "3. Check logs with: railway logs"