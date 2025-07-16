#!/bin/bash

# Simple TradeSense Test Script
echo "🚀 Starting TradeSense in Test Mode"
echo "=================================="

# Clean up
echo "🧹 Cleaning up previous sessions..."
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "npm.*dev" 2>/dev/null || true
sleep 2

# Start backend
echo ""
echo "🔧 Starting Backend..."
cd src/backend
source test_venv/bin/activate 2>/dev/null || python3 -m venv test_venv && source test_venv/bin/activate
pip install -q -r requirements.txt
python3 main.py &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

# Wait for backend
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    sleep 1
done

# Start frontend
echo ""
echo "🎨 Starting Frontend..."
cd ../../frontend
npm install --silent
npm run dev &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "=========================================="
echo "✅ TradeSense is running!"
echo "=========================================="
echo ""
echo "📍 Access the application at:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Test Credentials:"
echo "   Email: test@example.com"
echo "   Password: testpass123"
echo ""
echo "🛑 To stop: Press Ctrl+C or run ./stop.sh"
echo "=========================================="

# Keep script running
wait