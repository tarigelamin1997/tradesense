
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.trade import Trade
from services.critique_engine import CritiqueEngine
from .schemas import CritiqueResponse, CritiqueFeedbackRequest

logger = logging.getLogger(__name__)

class CritiqueService:
    def __init__(self, db: Session):
        self.db = db
        self.critique_engine = CritiqueEngine()
    
    async def get_trade_critique(self, trade_id: str, user_id: str, regenerate: bool = False) -> CritiqueResponse:
        """Get or generate critique for a trade"""
        
        # Get the trade
        trade = self.db.query(Trade).filter(
            Trade.id == trade_id,
            Trade.user_id == user_id
        ).first()
        
        if not trade:
            raise ValueError("Trade not found")
        
        # Check if critique exists and we don't need to regenerate
        if trade.ai_critique and not regenerate:
            critique_data = trade.ai_critique
        else:
            # Generate new critique
            critique_data = await self.critique_engine.generate_critique(trade)
            
            # Save to database
            trade.ai_critique = critique_data
            trade.critique_generated_at = datetime.now()
            trade.critique_confidence = critique_data.get("confidence", 5)
            
            self.db.commit()
            self.db.refresh(trade)
        
        return CritiqueResponse(**critique_data)
    
    async def submit_critique_feedback(
        self, 
        trade_id: str, 
        user_id: str, 
        feedback: CritiqueFeedbackRequest
    ) -> Dict[str, str]:
        """Submit feedback on critique quality"""
        
        trade = self.db.query(Trade).filter(
            Trade.id == trade_id,
            Trade.user_id == user_id
        ).first()
        
        if not trade:
            raise ValueError("Trade not found")
        
        # Store feedback in critique data
        if not trade.ai_critique:
            trade.ai_critique = {}
        
        if "feedback" not in trade.ai_critique:
            trade.ai_critique["feedback"] = []
        
        feedback_entry = {
            "helpful": feedback.helpful,
            "rating": feedback.rating,
            "feedback_text": feedback.feedback_text,
            "submitted_at": datetime.now().isoformat()
        }
        
        trade.ai_critique["feedback"].append(feedback_entry)
        
        # Mark as modified for SQLAlchemy
        trade.ai_critique = trade.ai_critique.copy()
        
        self.db.commit()
        
        logger.info(f"Feedback submitted for trade {trade_id} critique")
        
        return {"message": "Feedback submitted successfully"}
    
    async def get_critique_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics on critique usage and feedback"""
        
        trades_with_critique = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.ai_critique.isnot(None)
        ).all()
        
        if not trades_with_critique:
            return {
                "total_critiques": 0,
                "average_confidence": 0,
                "most_common_tags": [],
                "feedback_stats": {}
            }
        
        # Calculate statistics
        total_critiques = len(trades_with_critique)
        confidence_scores = [t.critique_confidence for t in trades_with_critique if t.critique_confidence]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Collect all tags
        all_tags = []
        feedback_count = 0
        helpful_count = 0
        
        for trade in trades_with_critique:
            if trade.ai_critique and "tags" in trade.ai_critique:
                all_tags.extend(trade.ai_critique["tags"])
            
            if trade.ai_critique and "feedback" in trade.ai_critique:
                for fb in trade.ai_critique["feedback"]:
                    feedback_count += 1
                    if fb.get("helpful"):
                        helpful_count += 1
        
        # Count tag frequency
        from collections import Counter
        tag_counts = Counter(all_tags)
        most_common_tags = [{"tag": tag, "count": count} for tag, count in tag_counts.most_common(10)]
        
        return {
            "total_critiques": total_critiques,
            "average_confidence": round(avg_confidence, 2),
            "most_common_tags": most_common_tags,
            "feedback_stats": {
                "total_feedback": feedback_count,
                "helpful_percentage": round((helpful_count / feedback_count * 100), 2) if feedback_count > 0 else 0
            }
        }
