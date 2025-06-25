
"""
Advanced trades API endpoints with filtering, pagination, and bulk operations
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import pandas as pd
import io

from backend.models.trade import Trade, TradeCreate, TradeResponse
from backend.services.analytics_service import AnalyticsService
from backend.api.deps import get_current_user, get_db
from backend.core.security import verify_token

router = APIRouter()
analytics_service = AnalyticsService()

@router.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    symbol: Optional[str] = Query(None),
    strategy: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    min_pnl: Optional[float] = Query(None),
    max_pnl: Optional[float] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trades with advanced filtering and pagination"""
    query = db.query(Trade).filter(Trade.user_id == current_user["user_id"])
    
    # Apply filters
    if symbol:
        query = query.filter(Trade.symbol.ilike(f"%{symbol}%"))
    if strategy:
        query = query.filter(Trade.strategy_tag.ilike(f"%{strategy}%"))
    if start_date:
        query = query.filter(Trade.entry_time >= start_date)
    if end_date:
        query = query.filter(Trade.entry_time <= end_date)
    if min_pnl is not None:
        query = query.filter(Trade.pnl >= min_pnl)
    if max_pnl is not None:
        query = query.filter(Trade.pnl <= max_pnl)
    
    trades = query.offset(skip).limit(limit).all()
    return trades

@router.post("/trades/bulk", response_model=dict)
async def bulk_upload_trades(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk upload trades from CSV/Excel file"""
    try:
        contents = await file.read()
        
        # Determine file type and read accordingly
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Validate and process trades
        trades_created = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                trade_data = {
                    "symbol": row.get("symbol"),
                    "entry_time": pd.to_datetime(row.get("entry_time")),
                    "exit_time": pd.to_datetime(row.get("exit_time")) if pd.notna(row.get("exit_time")) else None,
                    "entry_price": float(row.get("entry_price")),
                    "exit_price": float(row.get("exit_price")) if pd.notna(row.get("exit_price")) else None,
                    "quantity": float(row.get("quantity")),
                    "direction": row.get("direction", "long"),
                    "pnl": float(row.get("pnl")) if pd.notna(row.get("pnl")) else None,
                    "strategy_tag": row.get("strategy_tag"),
                    "confidence_score": int(row.get("confidence_score")) if pd.notna(row.get("confidence_score")) else None
                }
                
                # Create trade
                trade = Trade(**trade_data, user_id=current_user["user_id"])
                db.add(trade)
                trades_created += 1
                
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        db.commit()
        
        return {
            "success": True,
            "trades_created": trades_created,
            "errors": errors
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/analytics")
async def get_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive analytics for user's trades"""
    analytics = await analytics_service.get_user_analytics(
        user_id=current_user["user_id"],
        start_date=start_date,
        end_date=end_date
    )
    return analytics

@router.get("/performance/live")
async def get_live_performance(
    current_user: dict = Depends(get_current_user)
):
    """Get real-time performance metrics"""
    # This would integrate with live trading data
    return {
        "open_positions": 3,
        "daily_pnl": 1250.50,
        "unrealized_pnl": 340.25,
        "account_balance": 125000.00,
        "buying_power": 87500.00
    }
