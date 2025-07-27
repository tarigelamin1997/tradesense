#!/bin/bash

echo "🚀 Starting TradeSense Backend..."
echo "Port: ${PORT:-8000}"
echo "Environment: ${ENVIRONMENT:-development}"

# Export Python path
export PYTHONPATH=/app/src/backend

# Check if we should skip database initialization
if [ "$SKIP_DB_INIT" = "true" ]; then
    echo "⏭️  Skipping database initialization (SKIP_DB_INIT=true)"
else
    echo "🔄 Initializing database..."
    python -c "
try:
    from core.db.session import create_tables
    create_tables()
    print('✅ Database initialized')
except Exception as e:
    print(f'⚠️  Database init failed: {e}')
    print('   Continuing anyway - will retry on first request')
"
fi

# Start the application
echo "🌐 Starting Uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}