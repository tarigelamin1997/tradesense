#!/usr/bin/env python3
"""
Database initialization script for TradeSense backend.
"""

import sys
import os

# Add backend to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

try:
    from backend.core.db.session import engine, Base
    # Import all models through centralized registry - this ensures proper registration
    import backend.models  # This triggers all model imports and registration
    from backend.models import *  # Import all registered models
    
    print("🗄️ Initializing TradeSense Database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database tables created successfully!")
    print(f"📍 Database location: {engine.url}")
    
    # Test database connection
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as session:
        # Test query
        user_count = session.query(User).count()
        trade_count = session.query(Trade).count()
        
        print(f"📊 Current data: {user_count} users, {trade_count} trades")
    
    print("🎉 Database initialization complete!")
    
except Exception as e:
    print(f"❌ Database initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
