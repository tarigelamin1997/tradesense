from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from api.v1.leaderboard.service import LeaderboardService
from api.deps import get_current_user
from models.user import UserRead

router = APIRouter(tags=["Global Leaderboard"])

@router.get("/global")
async def get_global_leaderboard(
    limit: int = Query(50, ge=10, le=100),
    metric: str = Query("overall", regex="^(overall|consistency|win_rate|profit_factor|volume)$"),
    timeframe: str = Query("all_time", regex="^(all_time|30d|90d|1y)$"),
    current_user: UserRead = Depends(get_current_user)
):
    """Get global leaderboard rankings"""
    service = LeaderboardService()
    try:
        leaderboard = service.get_global_leaderboard(
            limit=limit,
            metric=metric,
            timeframe=timeframe
        )
        return leaderboard
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve leaderboard: {str(e)}"
        )

@router.get("/my-ranking")
async def get_my_ranking(
    current_user: UserRead = Depends(get_current_user)
):
    """Get current user's global ranking and stats"""
    service = LeaderboardService()
    try:
        ranking = service.get_user_ranking(current_user.id)
        return ranking
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve ranking: {str(e)}"
        )

@router.get("/cross-account")
async def get_cross_account_analytics(
    current_user: UserRead = Depends(get_current_user)
):
    """Get cross-account analytics for current user"""
    service = LeaderboardService()
    try:
        analytics = service.get_cross_account_analytics(current_user.id)
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cross-account analytics: {str(e)}"
        )

@router.get("/account-comparison")
async def get_account_comparison(
    current_user: UserRead = Depends(get_current_user)
):
    """Get performance comparison across user's accounts"""
    service = LeaderboardService()
    try:
        comparison = service.get_account_comparison(current_user.id)
        return comparison
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve account comparison: {str(e)}"
        )

@router.post("/opt-in")
async def opt_into_leaderboard(
    current_user: UserRead = Depends(get_current_user)
):
    """Opt user into global leaderboard"""
    service = LeaderboardService()
    try:
        result = service.opt_into_leaderboard(current_user.id)
        return {"message": "Successfully opted into leaderboard", "status": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to opt into leaderboard: {str(e)}"
        )

@router.post("/opt-out")
async def opt_out_of_leaderboard(
    current_user: UserRead = Depends(get_current_user)
):
    """Opt user out of global leaderboard"""
    service = LeaderboardService()
    try:
        result = service.opt_out_of_leaderboard(current_user.id)
        return {"message": "Successfully opted out of leaderboard", "status": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to opt out of leaderboard: {str(e)}"
        )
