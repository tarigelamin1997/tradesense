
#!/usr/bin/env python3
"""
Quick health check for TradeSense app
"""

def quick_health_check():
    """Perform quick health check of the application."""
    print("🔍 TradeSense Health Check")
    print("=" * 30)
    
    # Test core imports
    try:
        import streamlit as st
        print(f"✅ Streamlit: {st.__version__}")
    except Exception as e:
        print(f"❌ Streamlit: {e}")
        return False
    
    try:
        import pandas as pd
        print(f"✅ Pandas: {pd.__version__}")
    except Exception as e:
        print(f"❌ Pandas: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
    except Exception as e:
        print(f"❌ NumPy: {e}")
        return False
    
    # Test app import
    try:
        import app
        print("✅ TradeSense app module")
    except Exception as e:
        print(f"❌ TradeSense app: {e}")
        return False
    
    print("✅ Health check passed!")
    return True

if __name__ == "__main__":
    if quick_health_check():
        print("\n🚀 Ready to launch: python3 -m streamlit run app.py --server.port=5000 --server.address=0.0.0.0")
    else:
        print("\n⚠️ Issues detected. Run diagnostic.py for detailed analysis.")
