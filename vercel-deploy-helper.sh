#!/bin/bash

# Vercel Deployment Helper Script
# This script helps you deploy TradeSense frontend to Vercel

echo "🎆 TradeSense Frontend Deployment to Vercel"
echo "========================================="
echo ""

# Check if backend URL was provided as argument
if [ -n "$1" ]; then
    BACKEND_URL=$1
else
    read -p "Enter your Railway backend URL (e.g., https://tradesense-backend.up.railway.app): " BACKEND_URL
fi

echo ""
echo "🔧 Preparing Frontend Environment..."
cd frontend

# Create production environment file
cat > .env.production << EOF
# API Configuration
VITE_API_BASE_URL=$BACKEND_URL
VITE_APP_URL=https://tradesense.vercel.app

# Stripe Public Key (update with your real key)
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here

# App Info
VITE_APP_VERSION=2.0.0
VITE_APP_NAME=TradeSense

# Support
VITE_SUPPORT_EMAIL=support@tradesense.ai
VITE_CONTACT_EMAIL=contact@tradesense.ai

# Build Configuration
NODE_ENV=production
EOF

echo "✅ Created .env.production with backend URL: $BACKEND_URL"
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm i -g vercel
fi

echo "🚀 Starting Vercel Deployment..."
echo ""
echo "Follow these prompts:"
echo "1. Login to Vercel (if needed)"
echo "2. Set up and deploy? Yes"
echo "3. Which scope? Select your account"
echo "4. Link to existing project? No (first time) or Yes (if redeploying)"
echo "5. Project name? tradesense"
echo "6. Directory? ./ (current directory)"
echo "7. Build settings? Accept defaults"
echo ""

# Deploy to Vercel
vercel --prod

echo ""
echo "✅ Frontend Deployment Complete!"
echo ""
echo "🔄 Final Step: Update CORS in Railway"
echo "1. Go back to your Railway project"
echo "2. Click on your backend service"
echo "3. Go to Variables tab"
echo "4. Update CORS_ORIGINS_STR to: https://tradesense.vercel.app"
echo "5. Railway will automatically redeploy"
echo ""
echo "🎉 Congratulations! TradeSense is now live!"
echo ""
echo "🧪 Quick Tests:"
echo "1. Visit https://tradesense.vercel.app"
echo "2. Create an account"
echo "3. Test the feedback button (bottom-right)"
echo "4. Check admin panel at /admin/feedback"
