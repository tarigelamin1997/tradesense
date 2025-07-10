
#!/usr/bin/env python3
"""
TradeSense Development Environment Setup
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ Error running command {cmd}: {e}")
        return False

def main():
    """Setup development environment."""
    print("🚀 Setting up TradeSense Development Environment")
    print("=" * 50)
    
    # Create required directories
    directories = [
        "backend/logs",
        "frontend/public",
        "logs",
        "infra/nginx"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Backend setup
    print("\n📦 Setting up Backend...")
    backend_deps = [
        "fastapi",
        "uvicorn[standard]",
        "python-multipart", 
        "sqlalchemy",
        "psycopg2-binary",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "websockets"
    ]
    
    for dep in backend_deps:
        if run_command(f"python -m pip install --user {dep}"):
            print(f"✅ Installed: {dep}")
        else:
            print(f"❌ Failed to install: {dep}")
    
    # Frontend setup
    print("\n🎨 Setting up Frontend...")
    if Path("frontend/package.json").exists():
        if run_command("npm install", cwd="frontend"):
            print("✅ Frontend dependencies installed")
        else:
            print("❌ Failed to install frontend dependencies")
    
    # Database setup
    print("\n🗄️ Database Setup...")
    if run_command("python -c \"from backend.db.connection import init_database; init_database()\""):
        print("✅ Database initialized")
    else:
        print("❌ Database initialization failed")
    
    print("\n🎉 Development environment setup complete!")
    print("\nNext steps:")
    print("1. Run: python app.py (for Streamlit)")
    print("2. Or use the 'Full Stack Development' workflow for FastAPI + React")
    print("3. Or run: docker-compose -f infra/docker-compose.yml up")

if __name__ == "__main__":
    main()
