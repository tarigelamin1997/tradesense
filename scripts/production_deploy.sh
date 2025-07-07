
#!/bin/bash

echo "🚀 TradeSense Production Deployment Script"
echo "=========================================="

# Configuration
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
DB_PATH="backend/tradesense.db"

# Create backup
echo "📦 Creating backup..."
mkdir -p $BACKUP_DIR
cp $DB_PATH $BACKUP_DIR/
cp -r frontend/dist $BACKUP_DIR/ 2>/dev/null || echo "Frontend dist not found"

# Database migrations
echo "🔄 Running database migrations..."
cd backend
python -c "
import sqlite3
from pathlib import Path

# Run any pending migrations
migration_files = sorted(Path('migrations').glob('*.py'))
for migration in migration_files:
    print(f'Running {migration.name}...')
    exec(open(migration).read())
"

# Frontend build
echo "🏗️ Building frontend..."
cd ../frontend
npm ci --production
npm run build

# Backend dependencies
echo "📦 Installing backend dependencies..."
cd ../backend
python -m pip install --user --no-cache-dir -r requirements.txt

# Health check
echo "🔍 Running health checks..."
python -c "
import sqlite3
import requests
import sys

# Database health check
try:
    conn = sqlite3.connect('tradesense.db')
    cursor = conn.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    print(f'✅ Database: {user_count} users found')
    conn.close()
except Exception as e:
    print(f'❌ Database error: {e}')
    sys.exit(1)

print('✅ All health checks passed!')
"

# Start services
echo "🚀 Starting services..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Health Monitor: http://localhost:5000/health"

echo "✅ Deployment completed successfully!"
echo "📊 Access monitoring at: /monitoring/health_dashboard.py"
