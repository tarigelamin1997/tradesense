
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from backend.core.db.session import get_db
from backend.api.deps import get_current_user
from backend.models.user import User
from backend.models.pattern_cluster import (
    PatternClusterCreate, PatternClusterUpdate, PatternClusterResponse
)
from .service import PatternService

router = APIRouter()

@router.post("/analyze", response_model=dict)
async def analyze_patterns(
    background_tasks: BackgroundTasks,
    min_trades: int = Query(20, ge=10, le=1000, description="Minimum trades required for analysis"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger pattern analysis for user's trades (runs in background)"""
    service = PatternService(db)
    
    # Check if user has enough trades
    trade_count = service.get_user_trade_count(current_user.id)
    if trade_count < min_trades:
        raise HTTPException(
            status_code=400, 
            detail=f"Need at least {min_trades} trades for pattern analysis. You have {trade_count}."
        )
    
    # Start background analysis
    background_tasks.add_task(
        service.run_pattern_analysis, 
        current_user.id, 
        min_trades
    )
    
    return {
        "message": "Pattern analysis started",
        "status": "processing",
        "trade_count": trade_count,
        "estimated_time": "2-5 minutes"
    }

@router.get("/status")
async def get_analysis_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status of pattern analysis"""
    service = PatternService(db)
    return service.get_analysis_status(current_user.id)

@router.get("/clusters", response_model=List[PatternClusterResponse])
async def get_pattern_clusters(
    cluster_type: Optional[str] = Query(None, description="Filter by cluster type"),
    min_avg_return: Optional[float] = Query(None, description="Filter by minimum average return"),
    max_avg_return: Optional[float] = Query(None, description="Filter by maximum average return"),
    saved_only: bool = Query(False, description="Show only saved patterns"),
    limit: int = Query(50, le=200, description="Limit results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's pattern clusters with optional filters"""
    service = PatternService(db)
    return service.get_pattern_clusters(
        user_id=current_user.id,
        cluster_type=cluster_type,
        min_avg_return=min_avg_return,
        max_avg_return=max_avg_return,
        saved_only=saved_only,
        limit=limit
    )

@router.get("/clusters/{cluster_id}", response_model=PatternClusterResponse)
async def get_pattern_cluster(
    cluster_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific pattern cluster"""
    service = PatternService(db)
    cluster = service.get_pattern_cluster(cluster_id=cluster_id, user_id=current_user.id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Pattern cluster not found")
    return cluster

@router.put("/clusters/{cluster_id}", response_model=PatternClusterResponse)
async def update_pattern_cluster(
    cluster_id: str,
    cluster_update: PatternClusterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a pattern cluster (save to playbook, add notes, etc.)"""
    service = PatternService(db)
    cluster = service.update_pattern_cluster(
        cluster_id=cluster_id,
        user_id=current_user.id,
        cluster_data=cluster_update
    )
    if not cluster:
        raise HTTPException(status_code=404, detail="Pattern cluster not found")
    return cluster

@router.delete("/clusters/{cluster_id}")
async def delete_pattern_cluster(
    cluster_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a pattern cluster"""
    service = PatternService(db)
    success = service.delete_pattern_cluster(cluster_id=cluster_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Pattern cluster not found")
    return {"message": "Pattern cluster deleted successfully"}

@router.get("/clusters/{cluster_id}/trades")
async def get_cluster_trades(
    cluster_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all trades in a specific pattern cluster"""
    service = PatternService(db)
    trades = service.get_cluster_trades(cluster_id=cluster_id, user_id=current_user.id)
    if trades is None:
        raise HTTPException(status_code=404, detail="Pattern cluster not found")
    return {"cluster_id": cluster_id, "trades": trades}

@router.get("/insights")
async def get_pattern_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get high-level insights from pattern analysis"""
    service = PatternService(db)
    return service.get_pattern_insights(current_user.id)

@router.post("/clusters/{cluster_id}/save-to-playbook")
async def save_cluster_to_playbook(
    cluster_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save a pattern cluster to user's trading playbook"""
    service = PatternService(db)
    success = service.save_to_playbook(cluster_id=cluster_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Pattern cluster not found")
    return {"message": "Pattern saved to playbook successfully"}
