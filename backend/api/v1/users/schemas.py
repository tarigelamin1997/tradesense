from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    trading_experience: Optional[str] = None
    risk_tolerance: Optional[str] = None
    trading_goals: Optional[List[str]] = None
    theme: Optional[str] = None
    primary_color: Optional[str] = None
    show_public_stats: Optional[bool] = None
    public_display_name: Optional[str] = None

class TradingStatsResponse(BaseModel):
    total_trades: int
    win_rate: float
    total_pnl: float
    avg_win: float
    avg_loss: float
    max_win: float
    max_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    current_streak: int
    best_streak: int
    total_trading_days: int
    active_days: int
    avg_daily_pnl: float
    consistency: float

class Achievement(BaseModel):
    id: str
    title: str
    description: str
    category: str
    earned: bool
    earned_date: Optional[str] = None
    progress: Optional[float] = None
    requirement: Optional[str] = None
    rarity: str

class UserProfileResponse(BaseModel):
    id: str
    username: str
    email: str
    display_name: str
    bio: str
    avatar: Optional[str]
    trading_experience: str
    risk_tolerance: str
    trading_goals: List[str]
    customization: Dict[str, Any]
    stats: TradingStatsResponse
    achievements: List[Achievement]
    created_at: datetime
    updated_at: datetime

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    display_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserRead(BaseModel):
    id: str
    email: str
    username: str
    created_at: Optional[datetime]
    first_name: Optional[str]
    last_name: Optional[str]
    is_verified: Optional[bool]

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[str]
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    password: Optional[str]

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    users: List[UserRead]

    class Config:
        from_attributes = True

class UserFilterParams(BaseModel):
    email: Optional[str]
    username: Optional[str]
    is_verified: Optional[bool]

    class Config:
        from_attributes = True

class UserStatsResponse(BaseModel):
    total_users: int
    active_users: Optional[int]
    verified_users: Optional[int]

    class Config:
        from_attributes = True
