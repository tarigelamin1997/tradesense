from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

class DailyEmotionReflectionBase(BaseModel):
    reflection_date: date
    mood_score: Optional[int] = Field(None, ge=-5, le=5, description="Mood scale from -5 (terrible) to +5 (excellent)")
    summary: Optional[str] = Field(None, max_length=1000, description="Daily reflection summary")
    dominant_emotion: Optional[str] = Field(None, max_length=50)

class DailyEmotionReflectionCreate(DailyEmotionReflectionBase):
    pass

class DailyEmotionReflectionUpdate(BaseModel):
    mood_score: Optional[int] = Field(None, ge=-5, le=5)
    summary: Optional[str] = Field(None, max_length=1000)
    dominant_emotion: Optional[str] = Field(None, max_length=50)

class DailyEmotionReflectionResponse(DailyEmotionReflectionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
