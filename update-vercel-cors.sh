#!/bin/bash

# Update CORS settings for all Railway services to include Vercel URL

VERCEL_URL="https://tradesense-3pu3bg5ll-tarig-ahmeds-projects.vercel.app"
CORS_ORIGINS="http://localhost:3001,http://localhost:5173,https://tradesense.vercel.app,https://tradesense.ai,https://www.tradesense.ai,$VERCEL_URL"

echo "Updating CORS settings for all services..."
echo "Adding Vercel URL: $VERCEL_URL"

# Update Gateway service
echo "Updating Gateway service..."
railway variables set CORS_ORIGINS_STR="$CORS_ORIGINS" -s tradesense-gateway

# Update Auth service
echo "Updating Auth service..."
railway variables set CORS_ORIGINS_STR="$CORS_ORIGINS" -s tradesense-auth

# Update Trading service
echo "Updating Trading service..."
railway variables set CORS_ORIGINS_STR="$CORS_ORIGINS" -s tradesense-trading

# Update Analytics service
echo "Updating Analytics service..."
railway variables set CORS_ORIGINS_STR="$CORS_ORIGINS" -s tradesense-analytics

# Update Market Data service
echo "Updating Market Data service..."
railway variables set CORS_ORIGINS_STR="$CORS_ORIGINS" -s tradesense-market-data

# Update Billing service
echo "Updating Billing service..."
railway variables set CORS_ORIGINS_STR="$CORS_ORIGINS" -s tradesense-billing

# Update AI service
echo "Updating AI service..."
railway variables set CORS_ORIGINS_STR="$CORS_ORIGINS" -s tradesense-ai

echo "✅ CORS settings updated for all services!"
echo "The services will restart automatically with the new settings."