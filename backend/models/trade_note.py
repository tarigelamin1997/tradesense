"""
Trade note model for attaching notes to trades
"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from core.db.session import Base
import uuid


class TradeNote(Base):
    __tablename__ = "trade_notes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    trade_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())