
#!/usr/bin/env python3
"""
TradeSense Diagnostic Tool
Run this to check your environment and identify issues
"""

import sys
import os
import subprocess
import importlib

def check_python_environment():
    """Check Python environment setup."""
    print("🐍 Python Environment Check")
    print(f"Python Version: {sys.version}")
    print(f"Python Path: {sys.executable}")
    print(f"Working Directory: {os.getcwd()}")
    print()

def check_required_modules():
    """Check if all required modules are available."""
    print("📦 Module Availability Check")
    required_modules = [
        'streamlit', 'pandas', 'numpy', 'plotly', 
        'datetime', 'logging', 'pathlib'
    ]
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
    print()

def check_file_structure():
    """Check critical file structure."""
    print("📁 File Structure Check")
    critical_files = [
        'app.py', 'startup.py', 'core/app_factory.py',
        'core-requirements.txt', '.replit'
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing!")
    print()

def check_environment_variables():
    """Check environment variables."""
    print("🔧 Environment Variables Check")
    important_vars = ['PYTHONPATH', 'PATH']
    
    for var in important_vars:
        value = os.environ.get(var, 'Not Set')
        print(f"{var}: {value}")
    print()

def run_diagnostics():
    """Run all diagnostic checks."""
    print("🏥 TradeSense Diagnostic Tool")
    print("=" * 50)
    
    check_python_environment()
    check_required_modules()
    check_file_structure()
    check_environment_variables()
    
    print("🎯 Recommendations:")
    print("1. If modules are missing, run: python3 -m pip install -r core-requirements.txt")
    print("2. If Python path issues, ensure symlink: ln -sf $(which python3) $HOME/.local/bin/python")
    print("3. If file issues, check file permissions and paths")
    print("4. Try running: streamlit run app.py --server.port=5000")

if __name__ == "__main__":
    run_diagnostics()
