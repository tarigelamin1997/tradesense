
"""
Strategy router - handles all strategy management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging

from backend.api.v1.strategies.schemas import (
    StrategyCreate, 
    StrategyRead, 
    StrategyUpdate,
    StrategyListResponse,
    StrategyAnalytics,
    TagAnalytics
)
from backend.api.v1.strategies.service import StrategyService
from backend.core.db.session import get_db
from backend.core.security import get_current_active_user
from backend.core.response import ResponseHandler, APIResponse
from backend.core.exceptions import TradeSenseException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/strategies", tags=["Strategy Management"])
strategy_service = StrategyService()


@router.post("/", response_model=StrategyRead, summary="Create Strategy")
async def create_strategy(
    strategy_data: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> StrategyRead:
    """
    Create a new trading strategy
    
    - **name**: Strategy name (required, unique per user)
    - **description**: Optional strategy description
    
    Returns the created strategy information
    """
    try:
        return await strategy_service.create_strategy(db, current_user["user_id"], strategy_data)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Create strategy endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=StrategyListResponse, summary="List Strategies")
async def list_strategies(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> StrategyListResponse:
    """
    List all strategies for the current user
    
    Returns all strategies created by the user
    """
    try:
        strategies = await strategy_service.list_strategies(db, current_user["user_id"])
        
        return StrategyListResponse(
            strategies=strategies,
            total=len(strategies)
        )
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"List strategies endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics", response_model=List[StrategyAnalytics], summary="Get Strategy Analytics")
async def get_strategy_analytics(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> List[StrategyAnalytics]:
    """
    Get performance analytics grouped by strategy
    
    Returns detailed performance metrics for each strategy
    """
    try:
        analytics = await strategy_service.get_strategy_analytics(db, current_user["user_id"])
        return [StrategyAnalytics(**stat) for stat in analytics]
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Strategy analytics endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tags/analytics", response_model=List[TagAnalytics], summary="Get Tag Analytics")
async def get_tag_analytics(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> List[TagAnalytics]:
    """
    Get performance analytics grouped by tag
    
    Returns performance metrics for each trade tag
    """
    try:
        analytics = await strategy_service.get_tag_analytics(db, current_user["user_id"])
        return [TagAnalytics(**stat) for stat in analytics]
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Tag analytics endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{strategy_id}", response_model=StrategyRead, summary="Get Strategy by ID")
async def get_strategy(
    strategy_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> StrategyRead:
    """
    Get a specific strategy by ID
    
    Users can only access their own strategies
    """
    try:
        return await strategy_service.get_strategy_by_id(db, current_user["user_id"], strategy_id)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Get strategy endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{strategy_id}", response_model=StrategyRead, summary="Update Strategy")
async def update_strategy(
    strategy_id: str,
    strategy_update: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> StrategyRead:
    """
    Update a trading strategy
    
    Users can only update their own strategies
    """
    try:
        return await strategy_service.update_strategy(
            db, current_user["user_id"], strategy_id, strategy_update
        )
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Update strategy endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{strategy_id}", response_model=APIResponse, summary="Delete Strategy")
async def delete_strategy(
    strategy_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> APIResponse:
    """
    Delete a trading strategy
    
    Users can only delete their own strategies.
    Cannot delete strategies that are referenced by existing trades.
    """
    try:
        result = await strategy_service.delete_strategy(db, current_user["user_id"], strategy_id)
        return ResponseHandler.success(
            data=result,
            message="Strategy deleted successfully"
        )
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Delete strategy endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
