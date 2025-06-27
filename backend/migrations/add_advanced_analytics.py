
#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from backend.core.db.session import engine, Base

class MarketRegime(Base):
    __tablename__ = 'market_regimes'
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    regime_type = Column(String(20), nullable=False)  # 'bull', 'bear', 'sideways'
    confidence_score = Column(Float, nullable=False)
    volatility_level = Column(String(10), nullable=False)  # 'low', 'medium', 'high'
    volume_trend = Column(String(10), nullable=False)  # 'increasing', 'decreasing', 'stable'
    created_at = Column(DateTime, nullable=False)

class ExecutionQualityMetric(Base):
    __tablename__ = 'execution_quality_metrics'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)  # Remove FK constraint for now
    trade_id = Column(String, nullable=False, index=True)  # Remove FK constraint for now
    entry_slippage = Column(Float)  # Difference between intended and actual entry price
    exit_slippage = Column(Float)   # Difference between intended and actual exit price
    hold_time_efficiency = Column(Float)  # How optimal was the hold time
    market_timing_score = Column(Float)   # How well timed was the entry/exit
    execution_grade = Column(String(2))   # A, B, C, D, F
    created_at = Column(DateTime, nullable=False)

def main():
    print("🔧 Adding Advanced Analytics Tables...")
    
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Advanced analytics tables created successfully")
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ['market_regimes', 'execution_quality_metrics']
        for table in required_tables:
            if table in tables:
                print(f"✅ Table '{table}' verified")
            else:
                print(f"❌ Table '{table}' missing")
        
        print("✅ Advanced analytics migration completed!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
