
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
        'datetime', 'logging', 'pathlib', 'bcrypt',
        'passlib', 'cryptography', 'jwt', 'psutil'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            missing_modules.append(module)
    
    print()
    return missing_modules

def check_file_structure():
    """Check critical file structure."""
    print("📁 File Structure Check")
    critical_files = [
        'app.py', 'startup.py', 'core/app_factory.py',
        'requirements.txt', 'core-requirements.txt', '.replit'
    ]
    
    missing_files = []
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            missing_files.append(file_path)
    
    print()
    return missing_files

def check_environment_variables():
    """Check environment variables."""
    print("🔧 Environment Variables Check")
    important_vars = ['PYTHONPATH', 'PATH', 'PYTHONUNBUFFERED']
    
    for var in important_vars:
        value = os.environ.get(var, 'Not Set')
        print(f"{var}: {value}")
    print()

def check_streamlit_health():
    """Check if Streamlit can be imported and run."""
    print("🌊 Streamlit Health Check")
    try:
        import streamlit as st
        print(f"✅ Streamlit version: {st.__version__}")
        
        # Test basic Streamlit functionality
        try:
            # This should work without actually starting the server
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            print("✅ Streamlit runtime accessible")
        except Exception as e:
            print(f"⚠️ Streamlit runtime issue: {e}")
            
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
    print()

def run_recovery_commands():
    """Suggest recovery commands based on diagnostics."""
    print("🚨 Emergency Recovery Commands")
    print("Run these if you're experiencing critical errors:")
    print()
    
    recovery_steps = [
        "# 1. Clean Python environment",
        "rm -rf ~/.local/lib/python* ~/.cache/pip",
        "",
        "# 2. Reinstall core dependencies", 
        "python3 -m pip install --user --no-cache-dir --force-reinstall streamlit==1.29.0",
        "python3 -m pip install --user --no-cache-dir --force-reinstall pandas==2.0.3",
        "",
        "# 3. Test application",
        "python3 -m streamlit run app.py --server.port=5000 --server.address=0.0.0.0"
    ]
    
    for step in recovery_steps:
        print(step)
    print()

def run_diagnostics():
    """Run all diagnostic checks."""
    print("🏥 TradeSense Diagnostic Tool")
    print("=" * 50)
    
    check_python_environment()
    missing_modules = check_required_modules()
    missing_files = check_file_structure()
    check_environment_variables()
    check_streamlit_health()
    
    # Summary and recommendations
    print("📊 Diagnostic Summary")
    print("=" * 30)
    
    if missing_modules:
        print(f"❌ Missing {len(missing_modules)} required modules")
        print("   Modules:", ", ".join(missing_modules))
    else:
        print("✅ All required modules available")
    
    if missing_files:
        print(f"❌ Missing {len(missing_files)} critical files")
        print("   Files:", ", ".join(missing_files))
    else:
        print("✅ All critical files present")
    
    print()
    print("🎯 Recommendations:")
    
    if missing_modules or missing_files:
        print("⚠️ Critical issues detected - run recovery commands")
        run_recovery_commands()
    else:
        print("✅ System appears healthy")
        print("1. Try running: python3 -m streamlit run app.py --server.port=5000")
        print("2. If issues persist, check logs in ./logs/ directory")
        print("3. Use 'Complete App Recovery' workflow for full reset")

if __name__ == "__main__":
    run_diagnostics()
