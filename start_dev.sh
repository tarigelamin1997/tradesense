#!/bin/bash
# Start development servers for TradeSense

echo "🚀 Starting TradeSense Development Environment..."

# Kill any existing processes on the ports
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

# Activate virtual environment
source venv/bin/activate

# Start Backend
echo "🔧 Starting Backend Server..."
cd src/backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create necessary directories if they don't exist
mkdir -p logs uploads temp

python3 -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start Frontend
echo "🎨 Starting Frontend Server..."
cd ../../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Development Environment Started!"
echo "📊 Backend PID: $BACKEND_PID (http://localhost:8000)"
echo "🖥️  Frontend PID: $FRONTEND_PID (http://localhost:5173)"
echo ""
echo "📝 Logs:"
echo "   - Backend API Docs: http://localhost:8000/api/docs"
echo "   - Frontend: http://localhost:5173"
echo ""
echo "🛑 Press Ctrl+C to stop both servers"

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set up trap to catch Ctrl+C
trap cleanup INT

# Wait for processes
wait