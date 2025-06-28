
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
    from backend.db.connection import engine, Base
    from backend.models.user import User
    from backend.models.trade import Trade
    from backend.models.feature_request import FeatureRequest
    from backend.models.playbook import Playbook
    from backend.models.tag import Tag
    from backend.models.portfolio import Portfolio
    from backend.models.trade_review import TradeReview
    from backend.models.trade_note import TradeNote
    from backend.models.milestone import Milestone
    from backend.models.mental_map import MentalMap
    from backend.models.pattern_cluster import PatternCluster
    from backend.models.strategy import Strategy
    from backend.models.trading_account import TradingAccount
    from backend.models.daily_emotion_reflection import DailyEmotionReflection
    
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
