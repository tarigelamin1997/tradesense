
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from backend.models.trade_review import (
    TradeReview, TradeReviewCreate, TradeReviewUpdate, 
    TradeReviewResponse, ReviewPatternAnalysis, ReviewInsights
)
from backend.models.trade import Trade

class TradeReviewService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_review(
        self, 
        trade_id: str, 
        user_id: str, 
        review_data: TradeReviewCreate
    ) -> TradeReviewResponse:
        """Create a new trade review"""
        
        # Verify trade exists and belongs to user
        trade = self.db.query(Trade).filter(
            and_(Trade.id == trade_id, Trade.user_id == user_id)
        ).first()
        
        if not trade:
            raise ValueError("Trade not found or access denied")
        
        # Check if review already exists
        existing_review = self.db.query(TradeReview).filter(
            TradeReview.trade_id == trade_id
        ).first()
        
        if existing_review:
            raise ValueError("Review already exists for this trade")
        
        # Create new review
        review = TradeReview(
            trade_id=trade_id,
            user_id=user_id,
            quality_score=review_data.quality_score,
            mistakes=review_data.mistakes,
            mood=review_data.mood,
            lesson_learned=review_data.lesson_learned,
            execution_vs_plan=review_data.execution_vs_plan
        )
        
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        
        return TradeReviewResponse.from_orm(review)
    
    async def update_review(
        self, 
        trade_id: str, 
        user_id: str, 
        review_data: TradeReviewUpdate
    ) -> Optional[TradeReviewResponse]:
        """Update an existing trade review"""
        
        review = self.db.query(TradeReview).filter(
            and_(
                TradeReview.trade_id == trade_id,
                TradeReview.user_id == user_id
            )
        ).first()
        
        if not review:
            return None
        
        # Update fields
        update_data = review_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(review, field, value)
        
        review.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(review)
        
        return TradeReviewResponse.from_orm(review)
    
    async def get_review_by_trade(
        self, 
        trade_id: str, 
        user_id: str
    ) -> Optional[TradeReviewResponse]:
        """Get review for a specific trade"""
        
        review = self.db.query(TradeReview).filter(
            and_(
                TradeReview.trade_id == trade_id,
                TradeReview.user_id == user_id
            )
        ).first()
        
        return TradeReviewResponse.from_orm(review) if review else None
    
    async def delete_review(self, trade_id: str, user_id: str) -> bool:
        """Delete a trade review"""
        
        review = self.db.query(TradeReview).filter(
            and_(
                TradeReview.trade_id == trade_id,
                TradeReview.user_id == user_id
            )
        ).first()
        
        if not review:
            return False
        
        self.db.delete(review)
        self.db.commit()
        return True
    
    async def get_user_reviews(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[TradeReviewResponse]:
        """Get all reviews for a user"""
        
        reviews = self.db.query(TradeReview).filter(
            TradeReview.user_id == user_id
        ).order_by(desc(TradeReview.created_at)).limit(limit).offset(offset).all()
        
        return [TradeReviewResponse.from_orm(review) for review in reviews]
    
    async def analyze_review_patterns(
        self, 
        user_id: str, 
        days: Optional[int] = 30
    ) -> ReviewPatternAnalysis:
        """Analyze review patterns for insights"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days) if days else None
        
        query = self.db.query(TradeReview).filter(TradeReview.user_id == user_id)
        if cutoff_date:
            query = query.filter(TradeReview.created_at >= cutoff_date)
        
        reviews = query.all()
        
        if not reviews:
            return ReviewPatternAnalysis(
                total_reviews=0,
                avg_quality_score=0.0,
                most_common_mistakes=[],
                mood_performance=[],
                quality_trend=[],
                improvement_areas=[],
                strengths=[]
            )
        
        # Calculate basic metrics
        total_reviews = len(reviews)
        avg_quality = sum(r.quality_score for r in reviews) / total_reviews
        
        # Analyze mistakes
        all_mistakes = []
        for review in reviews:
            if review.mistakes:
                all_mistakes.extend(review.mistakes)
        
        mistake_counter = Counter(all_mistakes)
        most_common_mistakes = [
            {
                "mistake": mistake,
                "count": count,
                "percentage": round((count / total_reviews) * 100, 1)
            }
            for mistake, count in mistake_counter.most_common(10)
        ]
        
        # Analyze mood vs performance
        mood_scores = defaultdict(list)
        for review in reviews:
            if review.mood:
                mood_scores[review.mood].append(review.quality_score)
        
        mood_performance = [
            {
                "mood": mood,
                "avg_quality": round(sum(scores) / len(scores), 2),
                "count": len(scores)
            }
            for mood, scores in mood_scores.items()
        ]
        mood_performance.sort(key=lambda x: x["avg_quality"], reverse=True)
        
        # Quality trend over time
        reviews_by_date = defaultdict(list)
        for review in reviews:
            date_key = review.created_at.date()
            reviews_by_date[date_key].append(review.quality_score)
        
        quality_trend = [
            {
                "date": str(date),
                "avg_quality": round(sum(scores) / len(scores), 2)
            }
            for date, scores in sorted(reviews_by_date.items())
        ]
        
        # Identify improvement areas and strengths
        improvement_areas = []
        strengths = []
        
        if most_common_mistakes:
            # Top 3 mistakes are improvement areas
            improvement_areas = [m["mistake"] for m in most_common_mistakes[:3]]
        
        if mood_performance:
            # Moods with high performance are strengths
            strengths = [
                m["mood"] for m in mood_performance 
                if m["avg_quality"] >= 4.0 and m["count"] >= 3
            ]
        
        return ReviewPatternAnalysis(
            total_reviews=total_reviews,
            avg_quality_score=round(avg_quality, 2),
            most_common_mistakes=most_common_mistakes,
            mood_performance=mood_performance,
            quality_trend=quality_trend,
            improvement_areas=improvement_areas,
            strengths=strengths
        )
    
    async def generate_insights(
        self, 
        user_id: str, 
        days: Optional[int] = 30
    ) -> ReviewInsights:
        """Generate actionable insights from review analysis"""
        
        patterns = await self.analyze_review_patterns(user_id, days)
        
        recommendations = []
        warnings = []
        achievements = []
        
        # Generate recommendations
        if patterns.improvement_areas:
            for area in patterns.improvement_areas[:2]:  # Top 2 areas
                recommendations.append(f"Focus on reducing '{area}' mistakes - appears in {patterns.most_common_mistakes[0]['percentage']}% of trades")
        
        if patterns.mood_performance:
            worst_mood = min(patterns.mood_performance, key=lambda x: x["avg_quality"])
            if worst_mood["avg_quality"] < 3.0:
                recommendations.append(f"Avoid trading when feeling '{worst_mood['mood']}' - average quality drops to {worst_mood['avg_quality']}")
        
        if patterns.avg_quality_score < 3.0:
            recommendations.append("Overall trade quality needs improvement - consider reducing position size until consistency improves")
        
        # Generate warnings for repeated patterns
        if patterns.most_common_mistakes:
            top_mistake = patterns.most_common_mistakes[0]
            if top_mistake["percentage"] > 30:
                warnings.append(f"High frequency of '{top_mistake['mistake']}' - occurs in {top_mistake['percentage']}% of trades")
        
        # Trend warnings
        if len(patterns.quality_trend) >= 7:  # At least a week of data
            recent_avg = sum(t["avg_quality"] for t in patterns.quality_trend[-7:]) / 7
            if recent_avg < patterns.avg_quality_score - 0.5:
                warnings.append("Quality score declining over past week - consider taking a break")
        
        # Identify achievements
        if patterns.avg_quality_score >= 4.0:
            achievements.append("Maintaining high trade quality - excellent execution!")
        
        if patterns.strengths:
            achievements.append(f"Strong performance when {', '.join(patterns.strengths)} - leverage these states")
        
        if len(patterns.quality_trend) >= 14:  # Two weeks of data
            recent_two_weeks = patterns.quality_trend[-14:]
            first_week = sum(t["avg_quality"] for t in recent_two_weeks[:7]) / 7
            second_week = sum(t["avg_quality"] for t in recent_two_weeks[7:]) / 7
            if second_week > first_week + 0.3:
                achievements.append("Quality improving week-over-week - keep up the momentum!")
        
        return ReviewInsights(
            patterns=patterns,
            recommendations=recommendations,
            warnings=warnings,
            achievements=achievements
        )
