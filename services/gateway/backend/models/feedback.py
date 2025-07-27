from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from database.database import Base

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    type = Column(String, nullable=False)  # bug, feature, performance, ux, other
    severity = Column(String, nullable=False)  # critical, high, medium, low
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="new")  # new, investigating, in_progress, resolved, closed
    
    # Context data
    url = Column(Text)
    user_agent = Column(Text)
    screen_resolution = Column(String)
    subscription_tier = Column(String)
    
    # Journey data (stored as JSON)
    previous_pages = Column(Text)  # JSON array
    last_actions = Column(Text)  # JSON array
    error_logs = Column(Text)  # JSON array
    
    # Additional details
    expected_behavior = Column(Text)
    actual_behavior = Column(Text)
    screenshot = Column(Text)  # Base64 encoded image
    email = Column(String)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    assigned_to = Column(String)
    
    # Analytics
    pattern_id = Column(String, ForeignKey("feedback_patterns.id"))
    duplicate_count = Column(Integer, default=0)
    affected_users = Column(Integer, default=1)
    first_reported_at = Column(DateTime, default=datetime.utcnow)
    last_reported_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="feedback_submissions")
    pattern = relationship("FeedbackPattern", back_populates="feedback_items")

class FeedbackPattern(Base):
    __tablename__ = "feedback_patterns"
    
    id = Column(String, primary_key=True)
    pattern_signature = Column(String, unique=True, index=True)
    pattern_type = Column(String)
    occurrences = Column(Integer, default=1)
    affected_users = Column(Integer, default=1)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    root_cause = Column(Text)
    resolution = Column(Text)
    
    # Relationships
    feedback_items = relationship("Feedback", back_populates="pattern")

class FeedbackImpact(Base):
    __tablename__ = "feedback_impact"
    
    feedback_id = Column(String, ForeignKey("feedback.id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    impact_score = Column(Integer)  # 1-10 based on user activity drop
    churn_risk = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)