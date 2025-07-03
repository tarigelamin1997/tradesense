"""
Trade Note schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

# Emotion tracking enums and models
EmotionType = Literal["Calm", "Excited", "Anxious", "Fearful", "Angry", "Confident", "Frustrated", "Euphoric", "Neutral"]
TriggerType = Literal["FOMO", "Hesitation", "Overconfidence", "Revenge", "Fear", "Greed", "Impatience", "Perfectionism", "Desperation"]

class EmotionData(BaseModel):
    emotion: Optional[EmotionType] = Field(None, description="Primary emotional state")
    confidence_score: Optional[int] = Field(None, ge=1, le=10, description="Confidence level (1-10)")
    mental_triggers: Optional[List[TriggerType]] = Field(default=[], description="Mental triggers affecting decision")

class JournalEntryBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Entry title")
    content: str = Field(..., min_length=1, description="Entry content")
    mood: Optional[str] = Field(None, max_length=50, description="Trader's mood")
    emotion_data: Optional[EmotionData] = Field(None, description="Psychological state data")

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalEntryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    mood: Optional[str] = Field(None, max_length=50)
    emotion_data: Optional[EmotionData] = Field(None, description="Psychological state data")

class JournalEntryResponse(JournalEntryBase):
    id: str
    trade_id: Optional[str]
    user_id: str
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

# Psychology analytics response models
class EmotionAnalytics(BaseModel):
    emotion_distribution: dict = Field(default={}, description="Distribution of emotions across entries")
    avg_confidence_score: Optional[float] = Field(None, description="Average confidence score")
    most_common_triggers: List[str] = Field(default=[], description="Most frequent mental triggers")
    confidence_vs_performance: dict = Field(default={}, description="Correlation between confidence and trade outcomes")
    emotional_trend: dict = Field(default={}, description="Emotional patterns over time")

class PsychologyInsights(BaseModel):
    total_emotional_entries: int = Field(0, description="Total entries with emotion data")
    dominant_emotion: Optional[str] = Field(None, description="Most common emotion")
    trigger_warning_count: int = Field(0, description="Entries with concerning triggers")
    confidence_consistency: float = Field(0.0, description="Consistency of confidence scores")
    recommendations: List[str] = Field(default=[], description="AI-generated recommendations")

# For including in trade responses
class TradeWithJournalResponse(BaseModel):
    id: str
    symbol: str
    direction: str
    quantity: float
    entry_price: float
    exit_price: Optional[float]
    entry_time: datetime
    exit_time: Optional[datetime]
    pnl: Optional[float]
    strategy_tag: Optional[str]
    notes: Optional[str]
    journal_entries: List[JournalEntryResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

class TradeNoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Note title")
    content: str = Field(..., min_length=1, description="Note content/body")
    mood: Optional[str] = Field(None, max_length=50, description="Emotional state")
    trade_id: Optional[str] = Field(None, description="Optional trade ID to link the note to")
    emotion: Optional[EmotionType] = Field(None, description="Primary emotional state")
    confidence_score: Optional[int] = Field(None, ge=1, le=10, description="Confidence level (1-10)")
    mental_triggers: Optional[List[TriggerType]] = Field(default=None, description="Mental triggers affecting decision")

class TradeNoteCreate(TradeNoteBase):
    pass

class TradeNoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    mood: Optional[str] = Field(None, max_length=50)
    trade_id: Optional[str] = Field(None)
    emotion: Optional[EmotionType] = Field(None)
    confidence_score: Optional[int] = Field(None, ge=1, le=10)
    mental_triggers: Optional[List[TriggerType]] = Field(default=None)

class TradeNoteRead(TradeNoteBase):
    id: str
    user_id: str
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

class TradeNoteListResponse(BaseModel):
    notes: List[TradeNoteRead]
    total: int
    skip: int
    limit: int

class MoodStatsResponse(BaseModel):
    mood_distribution: dict = Field(default_factory=dict, description="Distribution of moods across notes")
    most_common_mood: Optional[str] = Field(None, description="Most common mood")
    total_notes: int = Field(0, description="Total number of notes analyzed")