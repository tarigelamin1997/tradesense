
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from datetime import date

from models.daily_emotion_reflection import DailyEmotionReflection
from .schemas import DailyEmotionReflectionCreate, DailyEmotionReflectionUpdate

class DailyReflectionService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_or_update_reflection(
        self, 
        user_id: str, 
        reflection_data: DailyEmotionReflectionCreate
    ) -> DailyEmotionReflection:
        """Create or update daily reflection"""
        
        # Check if reflection already exists for this date
        existing = self.db.query(DailyEmotionReflection).filter(
            and_(
                DailyEmotionReflection.user_id == user_id,
                DailyEmotionReflection.reflection_date == reflection_data.reflection_date
            )
        ).first()
        
        if existing:
            # Update existing reflection
            for field, value in reflection_data.dict(exclude_unset=True).items():
                if field != 'reflection_date':  # Don't update the date
                    setattr(existing, field, value)
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new reflection
            reflection = DailyEmotionReflection(
                user_id=user_id,
                **reflection_data.dict()
            )
            
            self.db.add(reflection)
            self.db.commit()
            self.db.refresh(reflection)
            return reflection
    
    async def get_reflection_by_date(
        self, 
        user_id: str, 
        reflection_date: date
    ) -> Optional[DailyEmotionReflection]:
        """Get reflection for specific date"""
        
        return self.db.query(DailyEmotionReflection).filter(
            and_(
                DailyEmotionReflection.user_id == user_id,
                DailyEmotionReflection.reflection_date == reflection_date
            )
        ).first()
    
    async def update_reflection(
        self,
        user_id: str,
        reflection_date: date,
        update_data: DailyEmotionReflectionUpdate
    ) -> DailyEmotionReflection:
        """Update existing reflection"""
        
        reflection = await self.get_reflection_by_date(user_id, reflection_date)
        if not reflection:
            raise ValueError("Reflection not found for this date")
        
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(reflection, field, value)
        
        self.db.commit()
        self.db.refresh(reflection)
        return reflection
    
    async def delete_reflection(
        self,
        user_id: str,
        reflection_date: date
    ) -> bool:
        """Delete reflection for specific date"""
        
        reflection = await self.get_reflection_by_date(user_id, reflection_date)
        if reflection:
            self.db.delete(reflection)
            self.db.commit()
            return True
        return False
