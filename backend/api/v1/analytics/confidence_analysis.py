
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from backend.api.deps import get_db
from backend.models.trade import Trade
from backend.models.user import User

router = APIRouter()

@router.get("/confidence-calibration/{user_id}")
async def get_confidence_calibration(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Analyze how well user's confidence predictions match actual outcomes."""
    
    trades = db.query(Trade).filter(
        Trade.user_id == user_id,
        Trade.confidence_level.isnot(None)
    ).all()
    
    if not trades:
        return {"error": "No trades with confidence data found"}
    
    # Convert to DataFrame for analysis
    trade_data = []
    for trade in trades:
        trade_data.append({
            'confidence': trade.confidence_level,
            'pnl': trade.pnl,
            'outcome': 1 if trade.pnl > 0 else 0,
            'symbol': trade.symbol,
            'entry_date': trade.entry_date
        })
    
    df = pd.DataFrame(trade_data)
    
    # Confidence calibration analysis
    confidence_bins = [0, 20, 40, 60, 80, 100]
    df['confidence_bin'] = pd.cut(df['confidence'], bins=confidence_bins, labels=['0-20%', '21-40%', '41-60%', '61-80%', '81-100%'])
    
    calibration_data = []
    for bin_name in df['confidence_bin'].cat.categories:
        bin_data = df[df['confidence_bin'] == bin_name]
        if len(bin_data) > 0:
            actual_win_rate = bin_data['outcome'].mean()
            expected_confidence = bin_data['confidence'].mean()
            trade_count = len(bin_data)
            avg_pnl = bin_data['pnl'].mean()
            
            calibration_data.append({
                'confidence_range': bin_name,
                'expected_confidence': expected_confidence,
                'actual_win_rate': actual_win_rate * 100,
                'calibration_error': abs(expected_confidence - (actual_win_rate * 100)),
                'trade_count': trade_count,
                'avg_pnl': avg_pnl
            })
    
    # Overall calibration score
    total_calibration_error = sum([item['calibration_error'] * item['trade_count'] for item in calibration_data])
    total_trades = sum([item['trade_count'] for item in calibration_data])
    overall_calibration_score = 100 - (total_calibration_error / total_trades) if total_trades > 0 else 0
    
    return {
        'calibration_data': calibration_data,
        'overall_calibration_score': round(overall_calibration_score, 2),
        'total_trades_analyzed': total_trades,
        'insights': _generate_confidence_insights(calibration_data, overall_calibration_score)
    }

def _generate_confidence_insights(calibration_data: List[Dict], overall_score: float) -> List[str]:
    """Generate insights about confidence calibration."""
    insights = []
    
    if overall_score > 85:
        insights.append("🎯 Excellent confidence calibration! Your predictions closely match reality.")
    elif overall_score > 70:
        insights.append("👍 Good confidence calibration with room for improvement.")
    else:
        insights.append("⚠️ Poor confidence calibration - consider reviewing your prediction process.")
    
    # Find worst calibrated bin
    if calibration_data:
        worst_bin = max(calibration_data, key=lambda x: x['calibration_error'])
        if worst_bin['calibration_error'] > 20:
            insights.append(f"📊 Most miscalibrated range: {worst_bin['confidence_range']} - you're off by {worst_bin['calibration_error']:.1f}%")
    
    return insights

@router.get("/execution-quality/{user_id}")  
async def get_execution_quality(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Analyze trade execution quality and timing."""
    
    trades = db.query(Trade).filter(Trade.user_id == user_id).all()
    
    if not trades:
        return {"error": "No trades found"}
    
    execution_metrics = []
    
    for trade in trades:
        # Calculate metrics based on available data
        hold_time_hours = None
        if trade.exit_date and trade.entry_date:
            hold_time_hours = (trade.exit_date - trade.entry_date).total_seconds() / 3600
        
        execution_metrics.append({
            'symbol': trade.symbol,
            'entry_date': trade.entry_date,
            'pnl': trade.pnl,
            'hold_time_hours': hold_time_hours,
            'strategy': trade.strategy or 'Unknown'
        })
    
    df = pd.DataFrame(execution_metrics)
    
    # Execution quality analysis
    quality_analysis = {
        'avg_hold_time_hours': df['hold_time_hours'].mean() if df['hold_time_hours'].notna().any() else None,
        'quick_trades_performance': None,
        'long_trades_performance': None,
        'execution_insights': []
    }
    
    if df['hold_time_hours'].notna().any():
        # Define quick vs long trades (< 4 hours vs > 24 hours)
        quick_trades = df[df['hold_time_hours'] < 4]
        long_trades = df[df['hold_time_hours'] > 24]
        
        if len(quick_trades) > 0:
            quality_analysis['quick_trades_performance'] = {
                'count': len(quick_trades),
                'avg_pnl': quick_trades['pnl'].mean(),
                'win_rate': (quick_trades['pnl'] > 0).mean() * 100
            }
        
        if len(long_trades) > 0:
            quality_analysis['long_trades_performance'] = {
                'count': len(long_trades),
                'avg_pnl': long_trades['pnl'].mean(),
                'win_rate': (long_trades['pnl'] > 0).mean() * 100
            }
    
    return quality_analysis
