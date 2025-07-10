#!/usr/bin/env python3
"""
Model Verification Script for TradeSense Backend
Verifies all SQLAlchemy models are properly registered and can create tables.
"""

import sys
import os

# Add backend to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

try:
    print("🔍 Verifying TradeSense Model Registry...")
    
    # Import shared Base and engine
    from core.db.session import Base, engine
    
    # Import all models through centralized registry
    import models
    from models import *
    
    print(f"📊 Registered models: {len(Base.registry._class_registry)} classes")
    
    # Test table creation
    Base.metadata.create_all(bind=engine)
    
    print("✅ All models mapped and tables created successfully!")
    print("🎉 Model registry verification complete!")
    
    # Show registered models
    print("\n📋 Registered Models:")
    for name, cls in Base.registry._class_registry.items():
        if hasattr(cls, '__tablename__'):
            print(f"  • {name} -> {cls.__tablename__}")
    
except Exception as e:
    print(f"❌ Model registry verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
