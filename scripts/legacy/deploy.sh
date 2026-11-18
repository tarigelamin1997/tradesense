#!/bin/bash

# TradeSense Quick Deploy Script

echo "🚀 TradeSense Deployment Helper"
echo "==============================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists git; then
    echo "❌ Git is not installed"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is not installed"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is not installed"
    exit 1
fi

echo "✅ All prerequisites met!"
echo ""

# Git status check
echo "📦 Checking git status..."
if [[ -n $(git status -s) ]]; then
    echo "⚠️  You have uncommitted changes:"
    git status -s
    echo ""
    read -p "Do you want to commit them now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        read -p "Enter commit message: " commit_msg
        git commit -m "$commit_msg"
        git push origin main
    fi
else
    echo "✅ Working directory clean"
fi
echo ""

# Generate secrets if needed
if [ ! -f ".env.production" ]; then
    echo "🔐 No production env file found. Generating secrets..."
    ./scripts/generate-secrets.sh
    echo ""
    echo "⚠️  Please create .env.production with the generated secrets"
    echo ""
fi

# Deployment options
echo "🚀 Deployment Options:"
echo "1. Backend only (Railway)"
echo "2. Frontend only (Vercel)"
echo "3. Full deployment (Backend + Frontend)"
echo "4. Just prepare files"
echo ""
read -p "Select option (1-4): " deploy_option

case $deploy_option in
    1)
        echo "🚂 Deploying backend to Railway..."
        echo "Please follow these steps:"
        echo "1. Go to https://railway.app/new"
        echo "2. Connect your GitHub repo"
        echo "3. Add PostgreSQL and Redis"
        echo "4. Configure environment variables"
        echo ""
        echo "Backend URL will be: https://[your-app].railway.app"
        ;;
    2)
        echo "🎨 Deploying frontend to Vercel..."
        cd frontend
        
        # Check for API URL
        if [ ! -f ".env.production" ]; then
            read -p "Enter your backend URL (e.g., https://api.railway.app): " backend_url
            echo "VITE_API_BASE_URL=$backend_url" > .env.production
        fi
        
        # Deploy to Vercel
        npx vercel --prod
        ;;
    3)
        echo "🌟 Full deployment process..."
        echo ""
        echo "Step 1: Deploy backend first"
        echo "- Go to https://railway.app/new"
        echo "- Follow backend deployment steps"
        echo ""
        read -p "Press enter when backend is deployed..."
        
        read -p "Enter your Railway backend URL: " backend_url
        
        echo ""
        echo "Step 2: Deploying frontend..."
        cd frontend
        echo "VITE_API_BASE_URL=$backend_url" > .env.production
        npx vercel --prod
        
        echo ""
        echo "Step 3: Update CORS"
        echo "Go back to Railway and update CORS_ORIGINS_STR with your Vercel URL"
        ;;
    4)
        echo "📁 Preparing deployment files..."
        
        # Create production env examples if they don't exist
        if [ ! -f "src/backend/.env.production" ]; then
            cp .env.production.example src/backend/.env.production
            echo "✅ Created src/backend/.env.production (please edit)"
        fi
        
        if [ ! -f "frontend/.env.production" ]; then
            echo "VITE_API_BASE_URL=https://your-backend.railway.app" > frontend/.env.production
            echo "✅ Created frontend/.env.production (please edit)"
        fi
        
        echo ""
        echo "Files prepared! Next steps:"
        echo "1. Edit environment files with your values"
        echo "2. Run this script again to deploy"
        ;;
esac

echo ""
echo "📚 Resources:"
echo "- Deployment Guide: ./RAPID_DEPLOYMENT_GUIDE.md"
echo "- Deployment Checklist: ./DEPLOYMENT_CHECKLIST.md"
echo "- Railway Docs: https://docs.railway.app"
echo "- Vercel Docs: https://vercel.com/docs"
echo ""
echo "Need help? Create an issue on GitHub!"