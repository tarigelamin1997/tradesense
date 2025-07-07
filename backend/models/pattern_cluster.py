from sqlalchemy import Column, String, Float, DateTime, Text, JSON, Index
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Import shared Base
from backend.core.db.session import Base

class PatternCluster(Base):
    __tablename__ = "pattern_clusters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Cluster metadata
    name = Column(String, nullable=False)
    summary = Column(Text)
    cluster_type = Column(String, default="performance")  # performance, behavioral, temporal
    
    # Trade references
    trade_ids = Column(JSON)  # List of trade IDs in this cluster
    trade_count = Column(String, default="0")
    
    # Performance metrics
    avg_return = Column(Float)
    win_rate = Column(Float)
    total_pnl = Column(Float)
    risk_reward_ratio = Column(Float)
    
    # Pattern features
    pattern_features = Column(JSON)  # Dict of key features that define this cluster
    dominant_instrument = Column(String)
    dominant_time_window = Column(String)
    dominant_setup = Column(String)
    dominant_mood = Column(String)
    
    # Analysis metadata
    cluster_score = Column(Float)  # Silhouette score or similar clustering quality metric
    analysis_date = Column(DateTime, default=func.now())
    feature_weights = Column(JSON)  # Which features were most important for clustering
    
    # User interaction
    is_saved_to_playbook = Column(String, default="false")
    user_notes = Column(Text)
    user_rating = Column(String)  # 1-5 star rating by user
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_cluster_type', 'user_id', 'cluster_type'),
        Index('idx_user_performance', 'user_id', 'avg_return'),
        Index('idx_analysis_date', 'user_id', 'analysis_date'),
        {"extend_existing": True}
    )

# Pydantic models for API
class PatternClusterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    summary: Optional[str] = Field(None, max_length=1000)
    cluster_type: str = Field(default="performance", pattern="^(performance|behavioral|temporal|setup)$")
    trade_ids: List[str] = Field(default_factory=list)
    pattern_features: Optional[Dict[str, Any]] = Field(default_factory=dict)
    user_notes: Optional[str] = Field(None, max_length=500)
    user_rating: Optional[str] = Field(None, pattern="^[1-5]$")

class PatternClusterCreate(PatternClusterBase):
    pass

class PatternClusterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    summary: Optional[str] = Field(None, max_length=1000)
    user_notes: Optional[str] = Field(None, max_length=500)
    user_rating: Optional[str] = Field(None, pattern="^[1-5]$")
    is_saved_to_playbook: Optional[str] = Field(None, pattern="^(true|false)$")

class PatternClusterResponse(PatternClusterBase):
    id: str
    user_id: str
    trade_count: str
    avg_return: Optional[float]
    win_rate: Optional[float]
    total_pnl: Optional[float]
    risk_reward_ratio: Optional[float]
    dominant_instrument: Optional[str]
    dominant_time_window: Optional[str]
    dominant_setup: Optional[str]
    dominant_mood: Optional[str]
    cluster_score: Optional[float]
    analysis_date: datetime
    feature_weights: Optional[Dict[str, float]]
    is_saved_to_playbook: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
