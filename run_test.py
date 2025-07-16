#!/usr/bin/env python3
"""Simple script to run TradeSense for testing"""

import subprocess
import os
import sys
import time
import signal

def run_command(cmd, cwd=None):
    """Run a command and return the process"""
    print(f"Running: {cmd}")
    return subprocess.Popen(cmd, shell=True, cwd=cwd)

def main():
    print("🚀 Starting TradeSense Test Environment")
    print("=====================================")
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), "src/backend")
    
    # Start backend
    print("\n📦 Starting Backend...")
    backend_proc = run_command(
        "source venv/bin/activate && python main.py",
        cwd=backend_dir
    )
    
    # Wait for backend to start
    print("⏳ Waiting for backend to start...")
    time.sleep(5)
    
    # Check if backend is running
    import requests
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Backend is running!")
        else:
            print("❌ Backend health check failed")
    except:
        print("❌ Backend is not responding")
    
    # Start frontend
    print("\n🎨 Starting Frontend...")
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    frontend_proc = run_command(
        "npm run dev",
        cwd=frontend_dir
    )
    
    print("\n=====================================")
    print("✅ TradeSense is running!")
    print("=====================================")
    print("\n📍 Access points:")
    print("   Frontend: http://localhost:5173")
    print("   Backend API: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("\n📝 Test credentials:")
    print("   Email: test@example.com")
    print("   Password: testpass123")
    print("\n🛑 Press Ctrl+C to stop")
    print("=====================================")
    
    # Keep running until interrupted
    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("✅ Stopped all services")

if __name__ == "__main__":
    main()