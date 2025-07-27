from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class FeedbackType(str, Enum):
    bug = "bug"
    feature = "feature"
    performance = "performance"
    ux = "ux"
    other = "other"

class FeedbackSeverity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class FeedbackStatus(str, Enum):
    new = "new"
    investigating = "investigating"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"

class UserAction(BaseModel):
    type: str
    target: Optional[str] = None
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None

class ErrorLog(BaseModel):
    message: str
    stack: Optional[str] = None
    timestamp: datetime
    url: str

class FeedbackSubmit(BaseModel):
    type: FeedbackType
    severity: FeedbackSeverity
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    email: Optional[str] = None
    url: str
    user_agent: str
    screen_resolution: str
    previous_pages: List[str] = []
    last_actions: List[UserAction] = []
    error_logs: List[ErrorLog] = []
    screenshot: Optional[str] = None
    timestamp: datetime

class FeedbackResponse(BaseModel):
    trackingId: str
    message: str

class FeedbackItem(BaseModel):
    id: str
    user_id: Optional[str] = None
    type: str
    severity: str
    title: str
    description: str
    status: FeedbackStatus
    url: str
    user_agent: str
    screen_resolution: str
    subscription_tier: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    assigned_to: Optional[str] = None
    duplicate_count: int = 0
    affected_users: int = 1

class FeedbackPattern(BaseModel):
    id: str
    pattern_signature: str
    pattern_type: str
    occurrences: int
    affected_users: int
    first_seen: datetime
    last_seen: datetime
    root_cause: Optional[str] = None
    resolution: Optional[str] = None

class TopIssue(BaseModel):
    pattern_id: str
    title: str
    count: int
    severity: str

class TrendingIssue(BaseModel):
    pattern_id: str
    title: str
    growth_rate: float

class ResolutionTime(BaseModel):
    average_hours: float
    by_severity: Dict[str, float]

class UserImpact(BaseModel):
    total_affected: int
    by_tier: Dict[str, int]

class ChurnCorrelation(BaseModel):
    high_risk_patterns: List[str]
    estimated_revenue_impact: float

class FeedbackAnalytics(BaseModel):
    top_issues: List[TopIssue]
    trending_issues: List[TrendingIssue]
    critical_patterns: List[FeedbackPattern]
    resolution_time: ResolutionTime
    user_impact: UserImpact
    churn_correlation: ChurnCorrelation

class FeedbackUpdate(BaseModel):
    status: FeedbackStatus
    resolution_notes: Optional[str] = None

class PatternDetails(BaseModel):
    pattern: FeedbackPattern
    related_feedback: List[FeedbackItem]
    suggested_fixes: List[str]

class FeedbackHeatmapData(BaseModel):
    page: str
    issue_count: int
    severity_breakdown: Dict[str, int]

class ImpactAnalysis(BaseModel):
    affected_features: List[str]
    user_segments: Dict[str, int]
    revenue_at_risk: float
    churn_probability: float