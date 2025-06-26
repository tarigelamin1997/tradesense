from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import uuid

Base = declarative_base()

class Trade(Base):
    __tablename__ = "trades"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)

    # Trade identification
    symbol = Column(String, nullable=False, index=True)
    strategy_tag = Column(String, index=True)
    trade_id = Column(String, unique=True)

    # Trade details
    direction = Column(String, nullable=False)  # 'long' or 'short'
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)

    # Timing
    entry_time = Column(DateTime, nullable=False, index=True)
    exit_time = Column(DateTime, index=True)

    # Performance
    pnl = Column(Float, index=True)
    commission = Column(Float, default=0.0)
    net_pnl = Column(Float)

    # Risk metrics
    max_adverse_excursion = Column(Float)
    max_favorable_excursion = Column(Float)
    confidence_score = Column(Integer)

    # Account association
    account_id = Column(String, ForeignKey('trading_accounts.id'), index=True)

    # Metadata
    notes = Column(Text)
    tags = Column(JSON)  # List of strings stored as JSON (legacy)
    strategy_tag = Column(String, index=True)  # Reference to strategy name
    strategy_id = Column(String, index=True)  # Reference to strategy ID

    # AI Critique Data
    ai_critique = Column(JSON)  # Stores critique analysis
    critique_generated_at = Column(DateTime)
    critique_confidence = Column(Integer)  # 1-10 confidence score

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    account = relationship("TradingAccount", back_populates="trades")
    tag_objects = relationship("Tag", secondary="trade_tags", back_populates="trades")

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_symbol', 'user_id', 'symbol'),
        Index('idx_user_date', 'user_id', 'entry_time'),
        Index('idx_pnl_filter', 'user_id', 'pnl'),
        Index('idx_user_strategy', 'user_id', 'strategy_tag'),
    )

# Pydantic models for API
class TradeBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    direction: str = Field(..., pattern="^(long|short)$")
    quantity: float = Field(..., gt=0)
    entry_price: float = Field(..., gt=0)
    exit_price: Optional[float] = Field(None, gt=0)
    entry_time: datetime
    exit_time: Optional[datetime] = None
    strategy_tag: Optional[str] = Field(None, max_length=50)
    confidence_score: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(default_factory=list, description="Trade tags for filtering and search")
    strategy_tag: Optional[str] = Field(None, max_length=100, description="Strategy identifier")
    account_id: Optional[str] = Field(None, description="Trading account ID")

    @validator('exit_time')
    def validate_exit_time(cls, v, values):
        if v and 'entry_time' in values and v <= values['entry_time']:
            raise ValueError('Exit time must be after entry time')
        return v

class TradeCreate(TradeBase):
    pass

class TradeUpdate(BaseModel):
    exit_price: Optional[float] = Field(None, gt=0)
    exit_time: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, description="Trade tags")
    strategy_tag: Optional[str] = Field(None, max_length=100, description="Strategy identifier")

class TradeResponse(TradeBase):
    id: str
    user_id: str
    pnl: Optional[float]
    commission: Optional[float]
    net_pnl: Optional[float]
    tags: Optional[List[str]]
    strategy_tag: Optional[str]
    account_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True