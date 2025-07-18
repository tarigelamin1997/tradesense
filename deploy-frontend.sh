#!/bin/bash

echo "🚀 Deploying TradeSense Frontend to Vercel"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Move to frontend directory
cd frontend

# Check if backend is responding
echo "🔍 Checking backend availability..."
BACKEND_URL="https://tradesense-production.up.railway.app"
if curl -f "$BACKEND_URL/api/health" 2>/dev/null; then
    echo "✅ Backend is healthy!"
else
    echo "⚠️  Warning: Backend may not be fully ready yet"
    echo "   Continuing with deployment..."
fi

# Deploy to Vercel
echo -e "\n📦 Deploying to Vercel..."
vercel --prod

echo -e "\n✅ Deployment complete!"
echo "Next steps:"
echo "1. Get your Vercel URL from the output above"
echo "2. Update CORS settings in Railway with: railway variables set CORS_ORIGINS_STR=https://your-app.vercel.app"
echo "3. Configure custom domain in Vercel dashboard"