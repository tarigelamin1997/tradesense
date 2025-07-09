"""
Edge Strength Analytics API Router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date

from backend.core.db.session import get_db
from backend.models.trade import Trade
from backend.services.edge_strength import EdgeStrengthService
from backend.api.deps import get_current_user

router = APIRouter(prefix="/edge-strength", tags=["Edge Strength Analytics"])

@router.get("/")
async def get_edge_strength_analysis(
    user_id: str = Depends(get_current_user),
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    strategy_filter: Optional[str] = Query(None, description="Filter by specific strategy"),
    min_trades: Optional[int] = Query(10, description="Minimum trades per strategy"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive edge strength analysis for all strategies
    """
    try:
        # Build query
        query = db.query(Trade).filter(Trade.user_id == user_id)
        
        if start_date:
            query = query.filter(Trade.entry_time >= start_date)
        if end_date:
            query = query.filter(Trade.entry_time <= end_date)
        if strategy_filter:
            query = query.filter(Trade.strategy_tag == strategy_filter)
        
        trades = query.all()
        
        if not trades:
            return {
                "strategies": {},
                "summary": {
                    "total_strategies": 0,
                    "profitable_strategies": 0,
                    "strong_edge_strategies": 0,
                    "weak_edge_strategies": 0,
                    "best_strategy": None,
                    "worst_strategy": None,
                    "total_trades_analyzed": 0
                },
                "generated_at": datetime.now().isoformat(),
                "filters_applied": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "strategy_filter": strategy_filter,
                    "min_trades": min_trades
                }
            }
        
        # Initialize edge strength service
        edge_service = EdgeStrengthService()
        edge_service.minimum_trades_threshold = min_trades
        
        # Calculate edge strength analysis
        analysis = edge_service.calculate_edge_strength(trades)
        
        # Add filter info to response
        analysis["filters_applied"] = {
            "start_date": start_date,
            "end_date": end_date,
            "strategy_filter": strategy_filter,
            "min_trades": min_trades
        }
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Edge strength analysis failed: {str(e)}")

@router.get("/comparison")
async def get_strategy_comparison(
    user_id: str = Depends(get_current_user),
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    db: Session = Depends(get_db)
):
    """
    Get strategy comparison and recommendations
    """
    try:
        # Build query
        query = db.query(Trade).filter(Trade.user_id == user_id)
        
        if start_date:
            query = query.filter(Trade.entry_time >= start_date)
        if end_date:
            query = query.filter(Trade.entry_time <= end_date)
        
        trades = query.all()
        
        if not trades:
            return {
                "comparison": [],
                "insights": ["No trade data available for comparison"],
                "total_strategies_analyzed": 0
            }
        
        # Get strategy comparison
        edge_service = EdgeStrengthService()
        comparison = edge_service.get_strategy_comparison(trades)
        
        return comparison
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy comparison failed: {str(e)}")

@router.get("/strategy/{strategy_name}")
async def get_strategy_detailed_analysis(
    strategy_name: str,
    user_id: str = Depends(get_current_user),
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    db: Session = Depends(get_db)
):
    """
    Get detailed analysis for a specific strategy
    """
    try:
        # Build query for specific strategy
        query = db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.strategy_tag == strategy_name
        )
        
        if start_date:
            query = query.filter(Trade.entry_time >= start_date)
        if end_date:
            query = query.filter(Trade.entry_time <= end_date)
        
        trades = query.all()
        
        if not trades:
            raise HTTPException(
                status_code=404, 
                detail=f"No trades found for strategy '{strategy_name}'"
            )
        
        # Get detailed metrics for this strategy
        edge_service = EdgeStrengthService()
        detailed_metrics = edge_service._calculate_strategy_metrics(trades)
        
        # Add trade history
        trade_history = [
            {
                "id": trade.id,
                "symbol": trade.symbol,
                "entry_time": trade.entry_time.isoformat(),
                "pnl": trade.pnl,
                "direction": trade.direction,
                "confidence_score": trade.confidence_score
            }
            for trade in sorted(trades, key=lambda t: t.entry_time, reverse=True)
        ]
        
        return {
            "strategy_metrics": detailed_metrics,
            "trade_history": trade_history[:50],  # Last 50 trades
            "total_trades": len(trades),
            "analysis_period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy analysis failed: {str(e)}")

@router.get("/recommendations")
async def get_strategy_recommendations(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get actionable strategy recommendations
    """
    try:
        # Get all user trades
        trades = db.query(Trade).filter(Trade.user_id == user_id).all()
        
        if not trades:
            return {
                "recommendations": [],
                "action_items": ["Start tracking your trades with strategy tags"],
                "summary": "No trade data available for recommendations"
            }
        
        # Get edge analysis
        edge_service = EdgeStrengthService()
        analysis = edge_service.calculate_edge_strength(trades)
        strategies = analysis.get("strategies", {})
        
        recommendations = []
        action_items = []
        
        for strategy_name, metrics in strategies.items():
            edge_strength = metrics["edge_strength"]
            sample_size = metrics["total_trades"]
            
            if sample_size < 20:
                recommendations.append({
                    "strategy": strategy_name,
                    "type": "data_collection",
                    "priority": "medium",
                    "message": f"Collect more data - only {sample_size} trades recorded",
                    "target": "Aim for 30+ trades for reliable statistics"
                })
            elif edge_strength >= 70:
                recommendations.append({
                    "strategy": strategy_name,
                    "type": "scale_up",
                    "priority": "high",
                    "message": f"Strong edge detected ({edge_strength:.1f}%) - consider increasing position size",
                    "target": f"Current profit: ${metrics['total_pnl']:,.0f}"
                })
                action_items.append(f"🚀 Scale up '{strategy_name}' strategy")
            elif edge_strength <= 30:
                recommendations.append({
                    "strategy": strategy_name,
                    "type": "review_or_stop",
                    "priority": "high",
                    "message": f"Weak edge ({edge_strength:.1f}%) - review or consider stopping",
                    "target": f"Current loss: ${metrics['total_pnl']:,.0f}"
                })
                action_items.append(f"⚠️ Review '{strategy_name}' strategy")
        
        # General recommendations
        if len(strategies) == 1:
            action_items.append("📈 Consider diversifying with additional strategies")
        
        profitable_strategies = sum(1 for s in strategies.values() if s["total_pnl"] > 0)
        if profitable_strategies == 0:
            action_items.append("🔍 All strategies need review - consider paper trading new setups")
        
        return {
            "recommendations": recommendations,
            "action_items": action_items,
            "summary": f"Analyzed {len(strategies)} strategies across {sum(s['total_trades'] for s in strategies.values())} trades"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")
