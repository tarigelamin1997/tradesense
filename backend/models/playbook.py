from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from backend.core.db.session import Base

class PlaybookStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"

class Playbook(Base):
    __tablename__ = "playbooks"
    __table_args__ = ({"extend_existing": True},)

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    entry_criteria = Column(Text, nullable=False)
    exit_criteria = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(Enum(PlaybookStatus), default=PlaybookStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    trades = relationship("Trade", back_populates="playbook")
    user = relationship("User", back_populates="playbooks")

    def __repr__(self):
        return f"<Playbook(name='{self.name}', status='{self.status}')>"