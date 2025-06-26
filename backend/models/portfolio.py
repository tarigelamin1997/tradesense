
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    initial_balance = Column(Float, default=10000.0)
    current_balance = Column(Float, default=10000.0)
    total_pnl = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    equity_snapshots = relationship("EquitySnapshot", back_populates="portfolio", cascade="all, delete-orphan")
    
class EquitySnapshot(Base):
    __tablename__ = "equity_snapshots"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    balance = Column(Float, nullable=False)
    daily_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    trade_count = Column(Integer, default=0)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="equity_snapshots")
