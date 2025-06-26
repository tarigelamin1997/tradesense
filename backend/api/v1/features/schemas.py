
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class FeatureRequestCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    category: str = Field(..., regex="^(analytics|ui|integration|performance|security|other)$")

class FeatureRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    effort_estimate: Optional[str] = None
    business_value: Optional[str] = None
    admin_notes: Optional[str] = None
    estimated_completion: Optional[datetime] = None

class FeatureRequestResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    status: str
    priority: str
    upvotes: int
    downvotes: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    effort_estimate: Optional[str]
    business_value: Optional[str]
    admin_notes: Optional[str]
    estimated_completion: Optional[datetime]
    
    # Computed fields
    net_votes: int
    user_vote: Optional[str] = None  # Set by service based on current user
    
    class Config:
        from_attributes = True

class FeatureVoteCreate(BaseModel):
    vote_type: str = Field(..., regex="^(upvote|downvote)$")

class FeatureCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

class FeatureCommentResponse(BaseModel):
    id: str
    content: str
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class FeatureStatsResponse(BaseModel):
    total_requests: int
    by_status: dict
    by_category: dict
    top_voted: List[FeatureRequestResponse]
    recent_requests: List[FeatureRequestResponse]
