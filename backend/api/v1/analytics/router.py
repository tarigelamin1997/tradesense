from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date

from backend.core.db.session import get_db
from backend.core.security import get_current_user
from .service import AnalyticsService
from .schemas import AnalyticsSummaryResponse, AnalyticsFilters, TimelineResponse
from .edge_strength import get_edge_strength_analysis
from .streaks import get_streak_analysis
from .heatmap import get_heatmap_data
from .playbook_comparison import get_playbook_metrics

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)

@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    strategy_filter: Optional[str] = Query(None, description="Filter by strategy"),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive analytics summary for trading performance"""
    try:
        filters = AnalyticsFilters(
            start_date=start_date,
            end_date=end_date,
            strategy_filter=strategy_filter
        )

        summary = await service.get_analytics_summary(
            user_id=current_user["user_id"],
            filters=filters
        )

        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics calculation failed: {str(e)}")

@router.get("/emotion-impact")
async def get_emotion_impact(
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get emotional impact analysis on trading performance"""
    try:
        return await service.get_emotion_impact_analysis(current_user["user_id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Emotion analysis failed: {str(e)}")

@router.get("/strategy-performance")
async def get_strategy_performance(
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get detailed strategy performance breakdown"""
    try:
        return await service.get_strategy_performance_analysis(current_user["user_id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy analysis failed: {str(e)}")

@router.get("/confidence-correlation")
async def get_confidence_correlation(
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get confidence score vs performance correlation"""
    try:
        return await service.get_confidence_performance_correlation(current_user["user_id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Confidence analysis failed: {str(e)}")

@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline_analysis(
    start_date: Optional[date] = Query(None, description="Timeline start date"),
    end_date: Optional[date] = Query(None, description="Timeline end date"),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get timeline heatmap data with daily P&L and emotions"""
    try:
        return await service.get_timeline_analysis(
            user_id=current_user["user_id"],
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeline analysis failed: {str(e)}")

@router.get("/heatmap")
async def heatmap_endpoint(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await get_heatmap_data(start_date, end_date, db, current_user)

@router.get("/playbooks/{playbook_name}/metrics")
async def playbook_metrics_endpoint(
    playbook_name: str,
    time_range: str = "6M",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await get_playbook_metrics(playbook_name, time_range, db, current_user)

@router.get("/streak-analysis/{user_id}")
async def get_streak_analysis(
    user_id: str,
    timeframe: str = "3M",
    db: Session = Depends(get_db)
):
    """Get streak analysis for user"""
    try:
        analysis = await streak_service.get_streak_analysis(db, user_id, timeframe)
        return success_response(analysis)
    except Exception as e:
        logger.error(f"Error getting streak analysis: {e}")
        return error_response("Failed to get streak analysis", 500)

@router.get("/playbook-comparison/{user_id}")
async def get_playbook_comparison(
    user_id: str,
    timeframe: str = "3M",
    db: Session = Depends(get_db)
):
    """Get playbook comparison analysis"""
    try:
        from ..playbooks.service import PlaybookService
        playbook_service = PlaybookService()

        # Get all user trades with playbook info
        trades_query = db.query(Trade).filter(Trade.user_id == user_id)

        # Apply timeframe filter
        if timeframe != "ALL":
            days_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365}
            days = days_map.get(timeframe, 90)
            cutoff_date = datetime.now() - timedelta(days=days)
            trades_query = trades_query.filter(Trade.entry_time >= cutoff_date)

        trades = trades_query.all()

        # Group trades by playbook
        playbook_groups = {}
        for trade in trades:
            playbook = trade.playbook_tag or "No Playbook"
            if playbook not in playbook_groups:
                playbook_groups[playbook] = []
            playbook_groups[playbook].append(trade)

        # Calculate metrics for each playbook
        comparisons = []
        performance_timeline = []

        for playbook_name, playbook_trades in playbook_groups.items():
            if len(playbook_trades) < 3:  # Skip playbooks with too few trades
                continue

            total_trades = len(playbook_trades)
            winning_trades = [t for t in playbook_trades if t.pnl > 0]
            losing_trades = [t for t in playbook_trades if t.pnl <= 0]

            win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
            avg_pnl = sum(t.pnl for t in playbook_trades) / total_trades if total_trades > 0 else 0
            total_pnl = sum(t.pnl for t in playbook_trades)

            # Calculate profit factor
            gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
            gross_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 1
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit

            # Calculate other metrics
            pnl_values = [t.pnl for t in playbook_trades]
            avg_return = sum(pnl_values) / len(pnl_values) if pnl_values else 0
            std_dev = (sum((pnl - avg_return) ** 2 for pnl in pnl_values) / len(pnl_values)) ** 0.5 if len(pnl_values) > 1 else 0
            sharpe_ratio = avg_return / std_dev if std_dev > 0 else 0

            # Calculate consistency score (inverse of coefficient of variation)
            consistency_score = (1 - (std_dev / abs(avg_return))) * 100 if avg_return != 0 else 0
            consistency_score = max(0, min(100, consistency_score))

            # Calculate max drawdown
            running_pnl = 0
            peak = 0
            max_drawdown = 0
            for trade in sorted(playbook_trades, key=lambda x: x.entry_time):
                running_pnl += trade.pnl
                if running_pnl > peak:
                    peak = running_pnl
                drawdown = peak - running_pnl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

            # Calculate average hold time
            hold_times = []
            for trade in playbook_trades:
                if trade.exit_time and trade.entry_time:
                    hold_time = (trade.exit_time - trade.entry_time).total_seconds() / 3600  # in hours
                    hold_times.append(hold_time)
            avg_hold_time = sum(hold_times) / len(hold_times) if hold_times else 0

            comparisons.append({
                "playbook_name": playbook_name,
                "total_trades": total_trades,
                "win_rate": win_rate,
                "avg_pnl": avg_pnl,
                "total_pnl": total_pnl,
                "profit_factor": profit_factor,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
                "avg_hold_time": avg_hold_time,
                "best_month": "N/A",  # Placeholder
                "worst_month": "N/A",  # Placeholder
                "consistency_score": consistency_score
            })

        # Generate performance timeline data
        if trades:
            # Group trades by month for timeline
            monthly_data = {}
            for trade in trades:
                month_key = trade.entry_time.strftime("%Y-%m")
                if month_key not in monthly_data:
                    monthly_data[month_key] = {}

                playbook = trade.playbook_tag or "No Playbook"
                if playbook not in monthly_data[month_key]:
                    monthly_data[month_key][playbook] = 0
                monthly_data[month_key][playbook] += trade.pnl

            # Convert to timeline format
            for month, playbook_pnls in sorted(monthly_data.items()):
                timeline_entry = {"date": month}
                for playbook, pnl in playbook_pnls.items():
                    timeline_entry[playbook] = pnl
                performance_timeline.append(timeline_entry)

        return success_response({
            "comparisons": comparisons,
            "performance_timeline": performance_timeline
        })

    except Exception as e:
        logger.error(f"Error getting playbook comparison: {e}")
        return error_response("Failed to get playbook comparison", 500)

@router.get("/available-playbooks/{user_id}")
async def get_available_playbooks(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get list of available playbooks for user"""
    try:
        # Get unique playbook tags from user's trades
        playbooks = db.query(Trade.playbook_tag).filter(
            Trade.user_id == user_id,
            Trade.playbook_tag.isnot(None),
            Trade.playbook_tag != ""
        ).distinct().all()

        playbook_list = [p[0] for p in playbooks if p[0]]
        if not playbook_list:
            playbook_list = ["No Playbook"]  # Default if no playbooks found

        return success_response({"playbooks": playbook_list})

    except Exception as e:
        logger.error(f"Error getting available playbooks: {e}")
        return error_response("Failed to get available playbooks", 500)