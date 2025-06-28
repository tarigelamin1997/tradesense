
#!/usr/bin/env python3
"""
TradeSense Development Server Startup Script
Handles both backend and frontend initialization
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check Python dependencies
    try:
        import fastapi
        import uvicorn
        print("✅ Backend dependencies found")
    except ImportError as e:
        print(f"❌ Backend dependency missing: {e}")
        return False
    
    # Check if Node.js is available
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        print("✅ Node.js found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js not found")
        return False
    
    return True

def initialize_database():
    """Initialize the database"""
    print("🗄️ Initializing database...")
    try:
        from backend.db.connection import init_database
        if init_database():
            print("✅ Database ready")
            return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    
    return False

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting backend server...")
    
    backend_env = os.environ.copy()
    backend_env['PYTHONPATH'] = str(Path.cwd())
    
    backend_process = subprocess.Popen(
        [sys.executable, "backend/main.py"],
        env=backend_env,
        cwd=Path.cwd()
    )
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Check if backend is running
    try:
        import requests
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server running on http://localhost:8000")
            return backend_process
    except:
        pass
    
    print("⚠️ Backend may not be fully ready yet")
    return backend_process

def start_frontend():
    """Start the React frontend server"""
    print("🎨 Starting frontend server...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return None
    
    # Install dependencies if needed
    if not (frontend_dir / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        subprocess.run(["npm", "install", "--legacy-peer-deps"], cwd=frontend_dir)
    
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir
    )
    
    print("✅ Frontend server starting on http://localhost:3000")
    return frontend_process

def main():
    """Main development server startup"""
    print("🚀 TradeSense Development Server")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        print("⚠️ Database initialization failed, continuing anyway...")
    
    processes = []
    
    try:
        # Start backend
        backend_process = start_backend()
        if backend_process:
            processes.append(backend_process)
        
        # Start frontend
        frontend_process = start_frontend()
        if frontend_process:
            processes.append(frontend_process)
        
        if not processes:
            print("❌ Failed to start any servers")
            sys.exit(1)
        
        print("\n" + "=" * 40)
        print("🎉 TradeSense Development Environment Ready!")
        print("📱 Frontend: http://localhost:3000")
        print("🔧 Backend API: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/api/docs")
        print("=" * 40)
        print("Press Ctrl+C to stop all servers")
        
        # Wait for processes
        while True:
            time.sleep(1)
            # Check if any process died
            for process in processes[:]:
                if process.poll() is not None:
                    print(f"⚠️ Process {process.pid} exited")
                    processes.remove(process)
            
            if not processes:
                print("❌ All processes stopped")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("✅ Servers stopped")

if __name__ == "__main__":
    main()
