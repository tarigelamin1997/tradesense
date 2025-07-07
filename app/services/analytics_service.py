
"""
Analytics Service
Business logic for trade analytics and performance calculations
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging

from app.services.database_service import DatabaseService
from app.models.analytics import PerformanceMetrics, StreakAnalysis, RiskMetrics

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.db = DatabaseService()

    async def get_dashboard_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get main dashboard metrics"""
        trades = await self.db.get_user_trades(user_id)
        
        if not trades:
            return {
                "total_trades": 0,
                "total_pnl": 0,
                "win_rate": 0,
                "message": "No trades found. Upload your trade data to see analytics."
            }
        
        df = pd.DataFrame(trades)
        
        return {
            "total_trades": len(df),
            "total_pnl": df['pnl'].sum() if 'pnl' in df.columns else 0,
            "win_rate": (df['pnl'] > 0).mean() * 100 if 'pnl' in df.columns else 0,
            "best_trade": df['pnl'].max() if 'pnl' in df.columns else 0,
            "worst_trade": df['pnl'].min() if 'pnl' in df.columns else 0,
            "avg_trade": df['pnl'].mean() if 'pnl' in df.columns else 0
        }

    async def calculate_performance_metrics(
        self, 
        user_id: int, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        symbol: Optional[str] = None
    ) -> PerformanceMetrics:
        """Calculate detailed performance metrics"""
        trades = await self.db.get_user_trades(user_id)
        
        if not trades:
            return PerformanceMetrics(
                total_trades=0, win_rate=0, avg_win=0, avg_loss=0,
                profit_factor=0, sharpe_ratio=0, max_drawdown=0,
                total_pnl=0, best_trade=0, worst_trade=0
            )
        
        df = pd.DataFrame(trades)
        
        # Apply filters
        if start_date:
            df = df[pd.to_datetime(df['entry_time']).dt.date >= start_date]
        if end_date:
            df = df[pd.to_datetime(df['entry_time']).dt.date <= end_date]
        if symbol:
            df = df[df['symbol'] == symbol]
        
        if df.empty:
            return PerformanceMetrics(
                total_trades=0, win_rate=0, avg_win=0, avg_loss=0,
                profit_factor=0, sharpe_ratio=0, max_drawdown=0,
                total_pnl=0, best_trade=0, worst_trade=0
            )
        
        pnl = df['pnl'] if 'pnl' in df.columns else pd.Series([0] * len(df))
        wins = pnl[pnl > 0]
        losses = pnl[pnl < 0]
        
        return PerformanceMetrics(
            total_trades=len(df),
            win_rate=(len(wins) / len(df)) * 100 if len(df) > 0 else 0,
            avg_win=wins.mean() if len(wins) > 0 else 0,
            avg_loss=losses.mean() if len(losses) > 0 else 0,
            profit_factor=abs(wins.sum() / losses.sum()) if len(losses) > 0 and losses.sum() != 0 else 0,
            sharpe_ratio=self._calculate_sharpe_ratio(pnl),
            max_drawdown=self._calculate_max_drawdown(pnl.cumsum()),
            total_pnl=pnl.sum(),
            best_trade=pnl.max(),
            worst_trade=pnl.min()
        )

    async def generate_equity_curve(self, user_id: int, period: str = "daily") -> List[Dict]:
        """Generate equity curve data"""
        trades = await self.db.get_user_trades(user_id)
        
        if not trades:
            return []
        
        df = pd.DataFrame(trades)
        if 'pnl' not in df.columns or 'entry_time' not in df.columns:
            return []
        
        df['entry_time'] = pd.to_datetime(df['entry_time'])
        df = df.sort_values('entry_time')
        df['cumulative_pnl'] = df['pnl'].cumsum()
        
        # Group by period
        if period == "daily":
            grouped = df.groupby(df['entry_time'].dt.date).agg({
                'cumulative_pnl': 'last'
            }).reset_index()
        else:
            grouped = df[['entry_time', 'cumulative_pnl']]
        
        return [
            {
                "date": row['entry_time'].isoformat() if hasattr(row['entry_time'], 'isoformat') else str(row['entry_time']),
                "equity": row['cumulative_pnl']
            }
            for _, row in grouped.iterrows()
        ]

    async def analyze_streaks(self, user_id: int) -> StreakAnalysis:
        """Analyze winning/losing streaks"""
        trades = await self.db.get_user_trades(user_id)
        
        if not trades:
            return StreakAnalysis(
                current_streak=0, current_streak_type="none",
                max_winning_streak=0, max_losing_streak=0,
                avg_winning_streak=0, avg_losing_streak=0
            )
        
        df = pd.DataFrame(trades)
        if 'pnl' not in df.columns:
            return StreakAnalysis(
                current_streak=0, current_streak_type="none",
                max_winning_streak=0, max_losing_streak=0,
                avg_winning_streak=0, avg_losing_streak=0
            )
        
        df = df.sort_values('entry_time')
        df['is_win'] = df['pnl'] > 0
        
        # Calculate streaks
        streaks = []
        current_streak = 1
        current_type = df['is_win'].iloc[0]
        
        for i in range(1, len(df)):
            if df['is_win'].iloc[i] == current_type:
                current_streak += 1
            else:
                streaks.append((current_streak, current_type))
                current_streak = 1
                current_type = df['is_win'].iloc[i]
        
        streaks.append((current_streak, current_type))
        
        winning_streaks = [s[0] for s in streaks if s[1]]
        losing_streaks = [s[0] for s in streaks if not s[1]]
        
        return StreakAnalysis(
            current_streak=current_streak,
            current_streak_type="winning" if current_type else "losing",
            max_winning_streak=max(winning_streaks) if winning_streaks else 0,
            max_losing_streak=max(losing_streaks) if losing_streaks else 0,
            avg_winning_streak=np.mean(winning_streaks) if winning_streaks else 0,
            avg_losing_streak=np.mean(losing_streaks) if losing_streaks else 0
        )

    async def process_trade_upload(self, user_id: int, file_content: bytes, filename: str) -> Dict:
        """Process uploaded trade data"""
        try:
            # Read file based on extension
            if filename.endswith('.csv'):
                df = pd.read_csv(pd.io.common.BytesIO(file_content))
            else:
                df = pd.read_excel(pd.io.common.BytesIO(file_content))
            
            # Process and save trades
            trades_processed = 0
            for _, row in df.iterrows():
                trade_data = {
                    "user_id": user_id,
                    "symbol": row.get("symbol", "UNKNOWN"),
                    "side": row.get("side", row.get("direction", "LONG")).upper(),
                    "quantity": float(row.get("quantity", row.get("qty", 1))),
                    "entry_price": float(row.get("entry_price", 0)),
                    "exit_price": float(row.get("exit_price", 0)) if pd.notna(row.get("exit_price")) else None,
                    "entry_time": pd.to_datetime(row.get("entry_time", row.get("date"))),
                    "exit_time": pd.to_datetime(row.get("exit_time")) if pd.notna(row.get("exit_time")) else None,
                    "pnl": float(row.get("pnl", 0)),
                    "commission": float(row.get("commission", 0)),
                    "tags": str(row.get("tags", "")),
                    "notes": str(row.get("notes", ""))
                }
                
                await self.db.create_trade(trade_data)
                trades_processed += 1
            
            logger.info(f"Processed {trades_processed} trades for user {user_id}")
            return {
                "trades_count": trades_processed,
                "filename": filename,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Trade upload processing failed: {e}")
            raise

    def _calculate_sharpe_ratio(self, pnl_series: pd.Series) -> float:
        """Calculate Sharpe ratio"""
        if len(pnl_series) < 2:
            return 0
        
        returns = pnl_series.pct_change().dropna()
        if returns.std() == 0:
            return 0
        
        return (returns.mean() / returns.std()) * np.sqrt(252)  # Annualized

    def _calculate_max_drawdown(self, cumulative_pnl: pd.Series) -> float:
        """Calculate maximum drawdown"""
        if len(cumulative_pnl) == 0:
            return 0
        
        peak = cumulative_pnl.expanding().max()
        drawdown = (cumulative_pnl - peak) / peak.abs()
        return drawdown.min() * 100  # As percentage
