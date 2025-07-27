#!/bin/bash

echo "🚀 Starting TradeSense Backend (Simple Mode)..."
echo "Port: ${PORT:-8000}"
echo "Environment: ${ENVIRONMENT:-development}"

# Set Python path
export PYTHONPATH=/app/src/backend:$PYTHONPATH

# Skip all initialization - just start the server
echo "🌐 Starting Uvicorn server directly..."
exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}