#!/bin/bash

echo "🔧 Update Railway CORS Settings"
echo "==============================="

# Check if Vercel URL is provided
if [ -z "$1" ]; then
    echo "Usage: ./update-cors.sh <your-vercel-url>"
    echo "Example: ./update-cors.sh https://tradesense-abc123.vercel.app"
    exit 1
fi

VERCEL_URL=$1

# Build CORS string with all necessary origins
CORS_ORIGINS="$VERCEL_URL,https://tradesense.ai,https://www.tradesense.ai"

# Add localhost for development
if [ "$2" == "--with-localhost" ]; then
    CORS_ORIGINS="$CORS_ORIGINS,http://localhost:3000,http://localhost:5173"
fi

echo "Setting CORS origins to: $CORS_ORIGINS"

# Update Railway
railway variables set CORS_ORIGINS_STR="$CORS_ORIGINS"

echo "✅ CORS settings updated!"
echo ""
echo "You may need to restart the Railway service for changes to take effect:"
echo "railway restart"