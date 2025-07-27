#!/bin/bash
# Frontend deployment script for Vercel

set -e

echo "🚀 Deploying TradeSense Frontend to Vercel"
echo "========================================="

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf .vercel
rm -rf .svelte-kit
rm -rf node_modules

# Install dependencies
echo "Installing dependencies..."
npm install

# Build the project
echo "Building the project..."
npm run build

# Deploy to Vercel
echo "Deploying to Vercel..."
npx vercel --prod --yes

echo "✅ Deployment complete!"