from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.db.session import Base
from datetime import datetime
import uuid
import enum

class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"

class FeatureRequest(Base):
    __tablename__ = "feature_requests"
    __table_args__ = ({"extend_existing": True},)
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    status = Column(SQLEnum(RequestStatus), default=RequestStatus.PENDING)
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    
    # User who created the request
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    # user = relationship("backend.models.user.User")  # Disabled temporarily
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Development estimates
    effort_estimate = Column(String(20))  # small, medium, large, xl
    business_value = Column(String(20))   # low, medium, high
    
    # Admin notes
    admin_notes = Column(Text)
    estimated_completion = Column(DateTime)

    # Relationships - temporarily disabled to resolve SQLAlchemy conflicts
    # user = relationship("backend.models.user.User", back_populates="feature_requests")
    # votes = relationship("backend.models.feature_request.FeatureVote", back_populates="feature_request", cascade="all, delete-orphan")
    # comments = relationship("backend.models.feature_request.FeatureComment", back_populates="feature_request", cascade="all, delete-orphan")

class FeatureVote(Base):
    __tablename__ = "feature_votes"
    __table_args__ = ({"extend_existing": True},)
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    feature_request_id = Column(String, ForeignKey("feature_requests.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    vote_type = Column(String, nullable=False)  # 'upvote' or 'downvote'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships - temporarily disabled to resolve SQLAlchemy conflicts
    # feature_request = relationship("backend.models.feature_request.FeatureRequest", back_populates="votes")
    # user = relationship("backend.models.user.User")

class FeatureComment(Base):
    __tablename__ = "feature_comments"
    __table_args__ = ({"extend_existing": True},)
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    feature_request_id = Column(String, ForeignKey("feature_requests.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships - temporarily disabled to resolve SQLAlchemy conflicts
    # feature_request = relationship("backend.models.feature_request.FeatureRequest", back_populates="comments")
    # user = relationship("backend.models.user.User")
