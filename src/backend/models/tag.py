"""
Tag model for trade categorization and organization
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Table, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from backend.core.db.session import Base

# Junction table for many-to-many relationship between trades and tags
trade_tags = Table(
    'trade_tags',
    Base.metadata,
    Column('trade_id', String, ForeignKey('trades.id'), primary_key=True),
    Column('tag_id', String, ForeignKey('tags.id'), primary_key=True),
    Index('idx_trade_tags_trade', 'trade_id'),
    Index('idx_trade_tags_tag', 'tag_id'),
    extend_existing=True
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(String(200), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code like #FF5733
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship to trades through junction table
    # trades = relationship("backend.models.trade.Trade", secondary=trade_tags, back_populates="tag_objects")  # Disabled for now

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_tag_name', 'user_id', 'name'),
        Index('idx_tag_user_created', 'user_id', 'created_at'),
        # Ensure unique tag names per user
        Index('idx_unique_user_tag', 'user_id', 'name', unique=True),
        {"extend_existing": True}
    )
