
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class CritiqueRequest(BaseModel):
    regenerate: bool = False

class CritiqueResponse(BaseModel):
    summary: str
    suggestion: str
    confidence: int = Field(..., ge=1, le=10)
    tags: List[str]
    technical_analysis: str
    psychological_analysis: str
    risk_assessment: str
    generated_at: datetime
    version: str = "1.0"

class CritiqueFeedbackRequest(BaseModel):
    helpful: bool
    feedback_text: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
