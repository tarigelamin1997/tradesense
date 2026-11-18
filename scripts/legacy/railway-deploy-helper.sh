#!/bin/bash

# Railway Deployment Helper Script
# This script helps you deploy TradeSense backend to Railway

echo "🚂 TradeSense Backend Deployment to Railway"
echo "=========================================="
echo ""
echo "📋 Pre-deployment Checklist:"
echo "✅ All changes committed and pushed to GitHub"
echo "✅ Production secrets generated"
echo "✅ Deployment configuration ready (railway.json)"
echo ""
echo "🔗 Step 1: Open Railway Dashboard"
echo "Go to: https://railway.app/new"
echo ""
echo "Press Enter when you're on the Railway new project page..."
read

echo ""
echo "📦 Step 2: Deploy from GitHub"
echo "1. Click 'Deploy from GitHub repo'"
echo "2. Authorize Railway to access your GitHub (if needed)"
echo "3. Select repository: tarigelamin1997/tradesense"
echo "4. Select branch: backup-2025-01-14-day3"
echo ""
echo "Press Enter when you've selected your repository..."
read

echo ""
echo "🗄️ Step 3: Add PostgreSQL Database"
echo "1. Click 'New' button in your project"
echo "2. Select 'Database'"
echo "3. Choose 'Add PostgreSQL'"
echo "4. Wait for PostgreSQL to provision (~1 minute)"
echo ""
echo "Press Enter when PostgreSQL is ready..."
read

echo ""
echo "📮 Step 4: Add Redis"
echo "1. Click 'New' button again"
echo "2. Select 'Database'"
echo "3. Choose 'Add Redis'"
echo "4. Wait for Redis to provision (~1 minute)"
echo ""
echo "Press Enter when Redis is ready..."
read

echo ""
echo "🔐 Step 5: Configure Environment Variables"
echo "1. Click on your main service (not PostgreSQL or Redis)"
echo "2. Go to 'Variables' tab"
echo "3. Click 'RAW Editor'"
echo "4. Copy and paste the following environment variables:"
echo ""
echo "========== COPY EVERYTHING BELOW THIS LINE =========="
cat << 'EOF'
JWT_SECRET_KEY=<generate: openssl rand -hex 32>
SECRET_KEY=<generate: openssl rand -hex 32>
CORS_ORIGINS_STR=http://localhost:3000
ADMIN_EMAIL=support@tradesense.ai
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
ENVIRONMENT=production
PORT=8000
EOF
echo "========== COPY EVERYTHING ABOVE THIS LINE =========="
echo ""
echo "5. Click 'Save' after pasting"
echo ""
echo "Press Enter when environment variables are saved..."
read

echo ""
echo "🚀 Step 6: Deploy!"
echo "Railway will automatically start deploying your application."
echo "This usually takes 3-5 minutes."
echo ""
echo "Monitor the deployment in the 'Deployments' tab."
echo ""
echo "Press Enter when deployment is complete..."
read

echo ""
echo "🌐 Step 7: Get Your Backend URL"
echo "1. Go to the 'Settings' tab of your service"
echo "2. Under 'Domains', click 'Generate Domain'"
echo "3. Copy your backend URL (e.g., https://tradesense-backend.up.railway.app)"
echo ""
read -p "Enter your Railway backend URL: " BACKEND_URL

echo ""
echo "✅ Backend Deployment Complete!"
echo ""
echo "Your backend is now live at: $BACKEND_URL"
echo ""
echo "📝 Next Steps:"
echo "1. Update frontend/.env.production with:"
echo "   VITE_API_BASE_URL=$BACKEND_URL"
echo ""
echo "2. Deploy frontend to Vercel"
echo "3. Update CORS_ORIGINS_STR in Railway with your Vercel URL"
echo ""
echo "Ready to deploy frontend? Run: scripts/legacy/vercel-deploy-helper.sh"
