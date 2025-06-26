
#!/bin/bash

set -e

echo "🚀 TradeSense Deployment Script"
echo "================================"

# Configuration
ENVIRONMENT=${1:-staging}
VERSION=$(git describe --tags --always --dirty)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"
echo "Timestamp: $TIMESTAMP"

# Pre-deployment checks
echo "🔍 Running pre-deployment checks..."

# Check if all tests pass
echo "Running backend tests..."
cd backend && python -m pytest --tb=short && cd ..

echo "Running frontend tests..."
cd frontend && npm test -- --watchAll=false && cd ..

# Check if build succeeds
echo "Building frontend..."
cd frontend && npm run build && cd ..

# Backup current deployment (if production)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "📦 Creating backup of current deployment..."
    # Add backup logic here
fi

# Deploy to Replit
echo "🚀 Deploying to $ENVIRONMENT..."

# Update environment variables
case $ENVIRONMENT in
    "staging")
        export DATABASE_URL="$STAGING_DATABASE_URL"
        export FRONTEND_URL="$STAGING_FRONTEND_URL"
        ;;
    "production")
        export DATABASE_URL="$PRODUCTION_DATABASE_URL"
        export FRONTEND_URL="$PRODUCTION_FRONTEND_URL"
        ;;
esac

# Run database migrations
echo "📊 Running database migrations..."
cd backend && python -c "
from core.db.session import engine
from models import trade, user, portfolio
from sqlalchemy import create_engine
import os

# Create all tables
trade.Base.metadata.create_all(bind=engine)
user.Base.metadata.create_all(bind=engine)
portfolio.Base.metadata.create_all(bind=engine)
print('✅ Database migrations completed')
" && cd ..

# Start services
echo "🔄 Starting services..."
if [ "$ENVIRONMENT" = "production" ]; then
    # Production deployment
    echo "Starting production services..."
    # Add production start commands
else
    # Staging deployment
    echo "Starting staging services..."
    # Add staging start commands
fi

# Health check
echo "🏥 Running health checks..."
sleep 10

# Check backend health
curl -f http://localhost:8000/health || {
    echo "❌ Backend health check failed"
    exit 1
}

# Check frontend
curl -f http://localhost:3000 || {
    echo "❌ Frontend health check failed"
    exit 1
}

echo "✅ Deployment completed successfully!"
echo "Version $VERSION deployed to $ENVIRONMENT at $TIMESTAMP"

# Send notification (optional)
if [ -n "$SLACK_WEBHOOK" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🚀 TradeSense $VERSION deployed to $ENVIRONMENT\"}" \
        $SLACK_WEBHOOK
fi
