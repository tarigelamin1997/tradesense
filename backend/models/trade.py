
"""
Enhanced trade data models with validation and relationships
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import enum

Base = declarative_base()

class TradeDirection(enum.Enum):
    LONG = "long"
    SHORT = "short"

class TradeStatus(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    entry_time = Column(DateTime, nullable=False, index=True)
    exit_time = Column(DateTime, nullable=True)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    direction = Column(Enum(TradeDirection), nullable=False)
    pnl = Column(Float, nullable=True)
    commission = Column(Float, default=0.0)
    status = Column(Enum(TradeStatus), default=TradeStatus.OPEN)
    
    # Enhanced fields
    strategy_tag = Column(String(100), nullable=True, index=True)
    confidence_score = Column(Integer, nullable=True)  # 1-10
    notes = Column(Text, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    # Risk metrics
    position_size_percent = Column(Float, nullable=True)
    risk_reward_ratio = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_source = Column(String(50), default="manual")
    
    # Relationships
    user = relationship("User", back_populates="trades")
    trade_analytics = relationship("TradeAnalytics", back_populates="trade", uselist=False)

class TradeAnalytics(Base):
    __tablename__ = "trade_analytics"
    
    id = Column(Integer, primary_key=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), unique=True)
    
    # Performance metrics
    hold_time_minutes = Column(Integer)
    max_adverse_excursion = Column(Float)  # MAE
    max_favorable_excursion = Column(Float)  # MFE
    efficiency_ratio = Column(Float)
    
    # Behavioral indicators
    revenge_trade_flag = Column(Boolean, default=False)
    overconfidence_flag = Column(Boolean, default=False)
    
    # Market context
    market_volatility = Column(Float)
    sector_performance = Column(Float)
    
    trade = relationship("Trade", back_populates="trade_analytics")

# Pydantic models for API
class TradeCreate(BaseModel):
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    direction: TradeDirection
    strategy_tag: Optional[str] = None
    confidence_score: Optional[int] = None
    notes: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError('Confidence score must be between 1 and 10')
        return v
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v

class TradeResponse(BaseModel):
    id: int
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    direction: TradeDirection
    pnl: Optional[float]
    status: TradeStatus
    strategy_tag: Optional[str]
    confidence_score: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True
