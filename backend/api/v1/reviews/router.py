from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from backend.api.deps import get_current_user, get_db
from backend.models.user import User
from backend.models.trade_review import (
    TradeReviewCreate, TradeReviewUpdate, TradeReviewResponse,
    ReviewPatternAnalysis, ReviewInsights
)
from backend.api.v1.reviews.service import TradeReviewService

router = APIRouter(tags=["reviews"])

@router.post("/trades/{trade_id}", response_model=TradeReviewResponse)
async def create_trade_review(
    trade_id: str,
    review_data: TradeReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a review for a specific trade"""
    service = TradeReviewService(db)
    try:
        review = await service.create_review(
            trade_id=trade_id,
            user_id=str(current_user.id),
            review_data=review_data
        )
        return review
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create review: {str(e)}")

@router.put("/trades/{trade_id}", response_model=TradeReviewResponse)
async def update_trade_review(
    trade_id: str,
    review_data: TradeReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing trade review"""
    service = TradeReviewService(db)
    try:
        review = await service.update_review(
            trade_id=trade_id,
            user_id=str(current_user.id),
            review_data=review_data
        )
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        return review
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update review: {str(e)}")

@router.get("/trades/{trade_id}", response_model=Optional[TradeReviewResponse])
async def get_trade_review(
    trade_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get review for a specific trade"""
    service = TradeReviewService(db)
    review = await service.get_review_by_trade(
        trade_id=trade_id,
        user_id=str(current_user.id)
    )
    return review

@router.delete("/trades/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trade_review(
    trade_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a trade review"""
    service = TradeReviewService(db)
    success = await service.delete_review(
        trade_id=trade_id,
        user_id=str(current_user.id)
    )
    if not success:
        raise HTTPException(status_code=404, detail="Review not found")

@router.get("/analytics/patterns", response_model=ReviewPatternAnalysis)
async def get_review_patterns(
    days: Optional[int] = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze review patterns and trends"""
    service = TradeReviewService(db)
    try:
        patterns = await service.analyze_review_patterns(
            user_id=str(current_user.id),
            days=days
        )
        return patterns
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")

@router.get("/analytics/insights", response_model=ReviewInsights)
async def get_review_insights(
    days: Optional[int] = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get actionable insights from review analysis"""
    service = TradeReviewService(db)
    try:
        insights = await service.generate_insights(
            user_id=str(current_user.id),
            days=days
        )
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@router.get("/", response_model=List[TradeReviewResponse])
async def get_user_reviews(
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all reviews for the current user"""
    service = TradeReviewService(db)
    reviews = await service.get_user_reviews(
        user_id=str(current_user.id),
        limit=limit,
        offset=offset
    )
    return reviews
