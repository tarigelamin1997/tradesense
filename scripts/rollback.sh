
#!/bin/bash

set -e

echo "🔄 TradeSense Rollback Script"
echo "============================="

# Configuration
ENVIRONMENT=${1:-staging}
TARGET_VERSION=${2}

if [ -z "$TARGET_VERSION" ]; then
    echo "❌ Error: Target version required"
    echo "Usage: ./rollback.sh [environment] [version]"
    exit 1
fi

echo "Environment: $ENVIRONMENT"
echo "Rolling back to version: $TARGET_VERSION"

# Confirmation prompt for production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "⚠️  WARNING: You are about to rollback PRODUCTION!"
    read -p "Type 'CONFIRM' to proceed: " confirmation
    if [ "$confirmation" != "CONFIRM" ]; then
        echo "Rollback cancelled."
        exit 1
    fi
fi

# Stop current services
echo "🛑 Stopping current services..."
pkill -f "uvicorn\|npm\|node" || true

# Checkout target version
echo "📦 Checking out version $TARGET_VERSION..."
git fetch --all
git checkout $TARGET_VERSION

# Restore database backup
echo "📊 Restoring database..."
# Add database restore logic here

# Reinstall dependencies
echo "📦 Installing dependencies..."
cd backend && pip install -r requirements.txt && cd ..
cd frontend && npm install && cd ..

# Rebuild frontend
echo "🔨 Building frontend..."
cd frontend && npm run build && cd ..

# Start services
echo "🚀 Starting services..."
# Add service start commands here

# Health check
echo "🏥 Running health checks..."
sleep 10

curl -f http://localhost:8000/health || {
    echo "❌ Backend health check failed"
    exit 1
}

curl -f http://localhost:3000 || {
    echo "❌ Frontend health check failed"
    exit 1
}

echo "✅ Rollback to $TARGET_VERSION completed successfully!"

# Send notification
if [ -n "$SLACK_WEBHOOK" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🔄 TradeSense rolled back to $TARGET_VERSION in $ENVIRONMENT\"}" \
        $SLACK_WEBHOOK
fi
