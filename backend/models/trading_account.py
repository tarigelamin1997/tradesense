from sqlalchemy import Column, String, DateTime, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid
from backend.core.db.session import Base

class TradingAccount(Base):
    __tablename__ = "trading_accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)  # e.g., "Apex Main", "Sim NQ", "Funded MES"
    broker = Column(String)  # e.g., "Apex", "Interactive Brokers", "TradingView"
    account_type = Column(String)  # 'sim', 'funded', 'live', 'demo'
    account_number = Column(String)  # Optional external account ID
    is_active = Column(String, default="true")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    trades = relationship("Trade", back_populates="account")

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_accounts', 'user_id', 'is_active'),
        Index('idx_account_type', 'account_type'),
        {"extend_existing": True}
    )

# Pydantic models for API
class TradingAccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    broker: Optional[str] = Field(None, max_length=50)
    account_type: Optional[str] = Field(None, pattern="^(sim|funded|live|demo)$")
    account_number: Optional[str] = Field(None, max_length=50)

class TradingAccountCreate(TradingAccountBase):
    pass

class TradingAccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    broker: Optional[str] = Field(None, max_length=50)
    account_type: Optional[str] = Field(None, pattern="^(sim|funded|live|demo)$")
    account_number: Optional[str] = Field(None, max_length=50)
    is_active: Optional[str] = Field(None, pattern="^(true|false)$")

class TradingAccountResponse(TradingAccountBase):
    id: str
    user_id: str
    is_active: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
