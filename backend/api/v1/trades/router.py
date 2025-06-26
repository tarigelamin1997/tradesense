from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.core.db.session import get_db
from backend.core.security import get_current_user
from .service import TradeService
from .schemas import (
    TradeCreate, TradeUpdate, TradeResponse, TradeFilters, 
    TradeListResponse, TradePaginationResponse
)
from .confidence_calibration import ConfidenceCalibrationService
from pydantic import BaseModel
from uuid import UUID

router = APIRouter(prefix="/api/v1/trades", tags=["trades"])

def get_trade_service(db: Session = Depends(get_db)) -> TradeService:
    return TradeService(db)

@router.post("/", response_model=TradeResponse)
async def create_trade(
    trade_data: TradeCreate,
    current_user: dict = Depends(get_current_user),
    trade_service: TradeService = Depends(get_trade_service)
):
    """Create a new trade"""
    try:
        return trade_service.create_trade(
            user_id=current_user["user_id"],
            trade_data=trade_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create trade")

@router.get("/", response_model=List[dict])
async def get_trades(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    include_journal: bool = Query(False, description="Include journal entries"),
    current_user: dict = Depends(get_current_user),
    trade_service: TradeService = Depends(get_trade_service)
):
    """Get all trades for the current user"""
    return trade_service.get_user_trades(
        user_id=current_user["user_id"],
        limit=limit,
        offset=offset,
        include_journal=include_journal
    )

@router.get("/{trade_id}", response_model=dict)
async def get_trade_with_journal(
    trade_id: str,
    current_user: dict = Depends(get_current_user),
    trade_service: TradeService = Depends(get_trade_service)
):
    """Get a specific trade with all its journal entries"""
    trade = trade_service.get_trade_with_journal(
        trade_id=trade_id,
        user_id=current_user["user_id"]
    )

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    return trade

@router.put("/{trade_id}", response_model=TradeResponse)
async def update_trade(
    trade_id: str,
    update_data: TradeUpdate,
    current_user: dict = Depends(get_current_user),
    trade_service: TradeService = Depends(get_trade_service)
):
    """Update a trade"""
    try:
        return trade_service.update_trade(
            trade_id=trade_id,
            user_id=current_user["user_id"],
            update_data=update_data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update trade")

@router.delete("/{trade_id}")
async def delete_trade(
    trade_id: str,
    current_user: dict = Depends(get_current_user),
    trade_service: TradeService = Depends(get_trade_service)
):
    """Delete a trade and all its journal entries"""
    try:
        trade_service.delete_trade(
            trade_id=trade_id,
            user_id=current_user["user_id"]
        )
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
    trade_service: TradeService = Depends(get_trade_service)
):
    """Attach or detach a playbook from a trade."""
    try:
        return trade_service.attach_playbook(
            trade_id=trade_id,
            user_id=current_user["user_id"],
            playbook_id=request.playbook_id
        )
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
        return calibration_service.get_confidence_calibration(current_user["user_id"])
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
        return calibration_service.get_confidence_by_playbook(current_user["user_id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to calculate playbook confidence calibration")

# Adding the new route for execution quality analysis
@router.get("/execution-quality")
async def execution_quality(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get execution quality analysis for all user trades"""
    # Placeholder for execution quality analysis logic
    return {"message": "Execution quality analysis endpoint"}