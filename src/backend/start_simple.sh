#!/bin/bash

echo "🚀 Starting TradeSense Backend (Simple Mode)..."
echo "Port: ${PORT:-8000}"
echo "Environment: ${ENVIRONMENT:-development}"

# Set Python path
export PYTHONPATH=/app/src/backend:$PYTHONPATH

# Try minimal version first for debugging
if [ -f "main_minimal.py" ]; then
    echo "🔧 Using minimal backend for debugging..."
    exec python main_minimal.py
else
    echo "🌐 Starting Uvicorn server directly..."
    exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
fi