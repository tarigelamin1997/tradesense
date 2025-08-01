from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

# Import shared Base
from core.db.session import Base

class Portfolio(Base):
    __tablename__ = "portfolios"
    __table_args__ = ({"extend_existing": True},)
    
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
    
    # Relationships - temporarily disabled to resolve SQLAlchemy conflicts
    # user = relationship("backend.models.user.User", back_populates="portfolios")  # Disabled for now
    # equity_snapshots = relationship("backend.models.portfolio.EquitySnapshot", back_populates="portfolio", cascade="all, delete-orphan")
    
class EquitySnapshot(Base):
    __tablename__ = "equity_snapshots"
    __table_args__ = ({"extend_existing": True},)
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    balance = Column(Float, nullable=False)
    daily_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    trade_count = Column(Integer, default=0)
    
    # Relationships - temporarily disabled to resolve SQLAlchemy conflicts
    # portfolio = relationship("backend.models.portfolio.Portfolio", back_populates="equity_snapshots")
