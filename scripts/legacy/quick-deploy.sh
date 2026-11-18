#!/bin/bash

echo "⚡ Quick Railway Deploy"
echo "====================="

cd /home/tarigelamin/Desktop/tradesense

# Show current status
echo "Branch: $(git branch --show-current)"
echo "Last commit: $(git log -1 --oneline)"

# Quick deploy
echo -e "\n🚀 Deploying to Railway..."
railway up

echo -e "\n📊 Checking deployment status..."
railway logs --tail 20