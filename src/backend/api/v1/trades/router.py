from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from core.db.session import get_db
from api.deps import get_current_user
from api.v1.trades.service import TradesService
from .schemas import (
    TradeCreateRequest, TradeUpdateRequest, TradeResponse, TradeIngestRequest, TradeIngestResponse
)
from .confidence_calibration import ConfidenceCalibrationService
from pydantic import BaseModel, ValidationError
from uuid import UUID
from core.cache import cache_response, invalidate_cache_pattern
from .upload import router as upload_router

router = APIRouter(tags=["trades"])
router.include_router(upload_router, tags=["trades"])

def get_trade_service(db: Session = Depends(get_db)) -> TradesService:
    return TradesService(db)

@router.get("/", response_model=List[dict])
async def get_trades(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    include_journal: bool = Query(False, description="Include journal entries"),
    current_user: dict = Depends(get_current_user),
    trade_service: TradesService = Depends(get_trade_service)
):
    """Get all trades for the current user with caching"""
    return await trade_service.get_user_trades_optimized(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        include_journal=include_journal
    )

@router.post("/", response_model=TradeResponse, status_code=201)
async def create_trade(
    trade_data: TradeCreateRequest,
    current_user: dict = Depends(get_current_user),
    trade_service: TradesService = Depends(get_trade_service)
):
    """Create a new trade"""
    try:
        trade = await trade_service.create_trade(
            user_id=current_user.id,
            trade_data=trade_data
        )
        
        # Invalidate user-specific cache
        invalidate_cache_pattern(f"user:{current_user.id}")
        
        return trade
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create trade")

@router.post("/ingest", response_model=TradeIngestResponse, status_code=200)
async def ingest_trade(
    trade_data: TradeIngestRequest,
    current_user: dict = Depends(get_current_user),
    trade_service: TradesService = Depends(get_trade_service)
):
    """Ingest a trade (for bulk or API ingestion)"""
    try:
        result = await trade_service.ingest_trade(
            user_id=current_user.id,
            trade_data=trade_data
        )
        
        # Invalidate user-specific cache
        invalidate_cache_pattern(f"user:{current_user.id}")
        
        return result
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=ve.errors())
    except HTTPException as he:
        # If this is an auth error, force 401
        if he.status_code == 403:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=he.detail)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{trade_id}", response_model=dict)
async def get_trade_with_journal(
    trade_id: str,
    current_user: dict = Depends(get_current_user),
    trade_service: TradesService = Depends(get_trade_service)
):
    """Get a specific trade with all its journal entries"""
    trade = await trade_service.get_trade_with_journal(
        trade_id=trade_id,
        user_id=current_user.id
    )

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    return trade

@router.put("/{trade_id}", response_model=TradeResponse)
async def update_trade(
    trade_id: str,
    update_data: TradeUpdateRequest,
    current_user: dict = Depends(get_current_user),
    trade_service: TradesService = Depends(get_trade_service)
):
    """Update a trade"""
    try:
        result = await trade_service.update_trade(
            trade_id=trade_id,
            user_id=current_user.id,
            update_data=update_data
        )
        
        # Invalidate related cache
        invalidate_cache_pattern(f"user:{current_user.id}")
        invalidate_cache_pattern(f"trade_detail")
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update trade")

@router.delete("/{trade_id}")
async def delete_trade(
    trade_id: str,
    current_user: dict = Depends(get_current_user),
    trade_service: TradesService = Depends(get_trade_service)
):
    """Delete a trade and all its journal entries"""
    try:
        await trade_service.delete_trade(
            trade_id=trade_id,
            user_id=current_user.id
        )
        
        # Invalidate related cache
        invalidate_cache_pattern(f"user:{current_user.id}")
        invalidate_cache_pattern(f"trade_detail")
        
        return {"message": "Trade and journal entries deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete trade")

class AttachPlaybookRequest(BaseModel):
    playbook_id: Optional[UUID] = None

@router.put("/{trade_id}/playbook", response_model=TradeResponse)
async def attach_playbook_to_trade(
    trade_id: str,
    request: AttachPlaybookRequest,
    current_user: dict = Depends(get_current_user),
    trade_service: TradesService = Depends(get_trade_service)
):
    """Attach or detach a playbook from a trade."""
    try:
        result = await trade_service.attach_playbook(
            trade_id=trade_id,
            user_id=current_user.id,
            playbook_id=request.playbook_id
        )
        
        # Invalidate related cache
        invalidate_cache_pattern(f"user:{current_user.id}")
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to attach/detach playbook")

@router.get("/confidence-calibration")
async def get_confidence_calibration(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get confidence calibration analysis for the current user"""
    try:
        calibration_service = ConfidenceCalibrationService(db)
        return calibration_service.get_confidence_calibration(current_user.id)
    except Exception as e:
        if "No trades with confidence scores found" in str(e):
            raise HTTPException(status_code=404, detail="No trades with confidence scores found")
        raise HTTPException(status_code=500, detail="Failed to calculate confidence calibration")

@router.get("/confidence-calibration/by-playbook")
async def get_confidence_calibration_by_playbook(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get confidence calibration analysis grouped by playbook"""
    try:
        calibration_service = ConfidenceCalibrationService(db)
        return calibration_service.get_confidence_by_playbook(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to calculate playbook confidence calibration")

@router.get("/execution-quality")
async def execution_quality(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get execution quality analysis for all user trades"""
    try:
        from .execution_quality import ExecutionQualityService
        execution_service = ExecutionQualityService(db)
        return execution_service.get_execution_quality_analysis(current_user.id)
    except ValueError as e:
        if "No completed trades found" in str(e):
            raise HTTPException(status_code=404, detail="No completed trades found for execution analysis")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to analyze execution quality")

# Export router for FastAPI
__all__ = ["router"]