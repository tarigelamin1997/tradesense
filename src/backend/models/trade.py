from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID

# Import shared Base
from core.db.session import Base
from models.tag import trade_tags

class Trade(Base):
    __tablename__ = "trades"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)

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

    # Playbook association
    playbook_id = Column(String, ForeignKey('playbooks.id'), index=True)

    # Metadata
    notes = Column(Text)
    market_context = Column(JSON)  # Store market conditions as JSON

    # AI Critique Data
    ai_critique = Column(JSON)  # Stores critique analysis
    critique_generated_at = Column(DateTime)
    critique_confidence = Column(Integer)  # 1-10 confidence score

    # Emotional Tracking & Post-Trade Reflection
    emotional_tags = Column(JSON)  # List of emotional states: ["FOMO", "Fear", "Greed", etc.]
    reflection_notes = Column(Text)  # Written reflection/lesson learned
    emotional_score = Column(Integer)  # 1-10 emotional control score
    executed_plan = Column(Boolean)  # Did trader follow their plan?
    post_trade_mood = Column(String)  # Overall mood after trade
    reflection_timestamp = Column(DateTime)  # When reflection was added
    tags = Column(JSON)  # List of strings stored as JSON (legacy)
    strategy_id = Column(String, index=True)  # Reference to strategy ID

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships - temporarily disabled to resolve SQLAlchemy conflicts
    # user = relationship("backend.models.user.User", back_populates="trades")
    # account = relationship("backend.models.trading_account.TradingAccount", back_populates="trades")
    # mental_entries = relationship("backend.models.mental_map.MentalMapEntry", back_populates="trade")
    # playbook = relationship("backend.models.playbook.Playbook", back_populates="trades")
    # review = relationship("backend.models.trade_review.TradeReview", back_populates="trade", uselist=False)
    # tag_objects = relationship("backend.models.tag.Tag", secondary=trade_tags, back_populates="trades")  # Disabled for now

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_symbol', 'user_id', 'symbol'),
        Index('idx_user_date', 'user_id', 'entry_time'),
        Index('idx_user_trade_strategy', 'user_id', 'strategy_tag'),
        Index('idx_pnl_filter', 'user_id', 'pnl'),
        {"extend_existing": True}
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
    account_id: Optional[str] = Field(None, description="Trading account ID")
    playbook_id: Optional[str] = Field(None, description="Playbook ID for structured trading setup")

    # Emotional Tracking Fields
    emotional_tags: Optional[List[str]] = Field(default_factory=list, description="Emotional states during trade")
    reflection_notes: Optional[str] = Field(None, max_length=2000, description="Post-trade reflection")
    emotional_score: Optional[int] = Field(None, ge=1, le=10, description="Emotional control score 1-10")
    executed_plan: Optional[bool] = Field(None, description="Did trader follow their plan?")
    post_trade_mood: Optional[str] = Field(None, max_length=50, description="Overall mood after trade")

    @field_validator('exit_time')
    @classmethod
    def validate_exit_time(cls, v, values):
        entry_time = values.get('entry_time')
        if v and entry_time and v < entry_time:
            raise ValueError('Exit time cannot be before entry time')
        return v

    model_config = {
        "json_schema_extra": {
            # ... example ...
        }
    }

class TradeCreate(TradeBase):
    pass

class TradeUpdate(BaseModel):
    exit_price: Optional[float] = Field(None, gt=0)
    exit_time: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, description="Trade tags")
    strategy_tag: Optional[str] = Field(None, max_length=100, description="Strategy identifier")
    playbook_id: Optional[str] = Field(None, description="Playbook ID")

class TradeResponse(TradeBase):
    id: str
    user_id: str
    pnl: Optional[float]
    commission: Optional[float]
    net_pnl: Optional[float]
    tags: Optional[List[str]]
    strategy_tag: Optional[str]
    account_id: Optional[str]
    playbook_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }