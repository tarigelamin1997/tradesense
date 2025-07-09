"""
Streaks Analytics API Endpoint
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import logging

from backend.services.analytics.streak_analyzer import streak_analyzer
from backend.api.deps import get_current_user
from backend.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/streaks")
async def get_streak_analysis(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive streak analysis for the current user
    
    Returns:
        Streak metrics, consistency score, and insights
    """
    try:
        # This is a simplified version - in a real implementation,
        # you'd fetch trades from your database
        # For now, we'll return sample data structure
        
        # TODO: Replace with actual trade fetching logic
        # trades = fetch_user_trades(current_user.id)
        
        # Sample trades for demonstration
        sample_trades = [
            {
                "id": 1,
                "pnl": 150.0,
                "entry_time": "2024-01-15T09:30:00",
                "exit_time": "2024-01-15T10:15:00"
            },
            {
                "id": 2,
                "pnl": -75.0,
                "entry_time": "2024-01-15T11:00:00",
                "exit_time": "2024-01-15T11:45:00"
            },
            {
                "id": 3,
                "pnl": 200.0,
                "entry_time": "2024-01-16T09:30:00",
                "exit_time": "2024-01-16T10:30:00"
            }
        ]
        
        analysis = streak_analyzer.analyze_streaks(sample_trades)
        
        return {
            "status": "success",
            "data": analysis
        }
        
    except Exception as e:
        logger.error(f"Error in streak analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze streaks"
        )


@router.get("/streaks/summary")
async def get_streak_summary(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a quick summary of streak metrics
    """
    try:
        # Sample data - replace with actual implementation
        return {
            "status": "success",
            "data": {
                "current_streak": 3,
                "current_streak_type": "win",
                "consistency_score": 72,
                "status_message": "🔥 3 Wins in a Row",
                "recommendation": "Consider maintaining position sizes"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in streak summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get streak summary"
        )
