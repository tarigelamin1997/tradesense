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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False)
    entry_criteria = Column(Text, nullable=False)
    exit_criteria = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(Enum(PlaybookStatus), default=PlaybookStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    trades = relationship("Trade", back_populates="playbook")

    def __repr__(self):
        return f"<Playbook(name='{self.name}', status='{self.status}')>"