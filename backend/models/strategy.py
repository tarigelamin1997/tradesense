"""
Strategy model for trade strategy management
"""
from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.sql import func
from core.db.session import Base
import uuid


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_strategy', 'user_id', 'name'),
        Index('idx_user_created', 'user_id', 'created_at'),
    )
