from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class FeatureRequest(Base):
    __tablename__ = "feature_requests"
    __table_args__ = ({"extend_existing": True},)
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # analytics, ui, integration, etc.
    status = Column(String(20), default="proposed")  # proposed, reviewing, approved, in_progress, completed, rejected
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    
    # User who created the request
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="feature_requests")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Development estimates
    effort_estimate = Column(String(20))  # small, medium, large, xl
    business_value = Column(String(20))   # low, medium, high
    
    # Admin notes
    admin_notes = Column(Text)
    estimated_completion = Column(DateTime)

class FeatureVote(Base):
    __tablename__ = "feature_votes"
    __table_args__ = ({"extend_existing": True},)
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    feature_request_id = Column(String, ForeignKey("feature_requests.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    vote_type = Column(String(10), nullable=False)  # upvote, downvote
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    feature_request = relationship("FeatureRequest")
    user = relationship("User")

class FeatureComment(Base):
    __tablename__ = "feature_comments"
    __table_args__ = ({"extend_existing": True},)
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    feature_request_id = Column(String, ForeignKey("feature_requests.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    feature_request = relationship("FeatureRequest")
    user = relationship("User")
