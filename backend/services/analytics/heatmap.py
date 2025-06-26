
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import numpy as np
from collections import defaultdict

from backend.models.trade import Trade

logger = logging.getLogger(__name__)

class HeatmapAnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        
    async def generate_heatmap_data(
        self, 
        user_id: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive heatmap data for time and symbol analysis"""
        
        # Get base trade query with filters
        trade_query = self.db.query(Trade).filter(Trade.user_id == user_id)
        
        if start_date:
            trade_query = trade_query.filter(Trade.entry_time >= start_date)
        if end_date:
            trade_query = trade_query.filter(Trade.entry_time <= end_date)
            
        trades = trade_query.all()
        
        if not trades:
            return self._empty_heatmap_response()
        
        # Convert to DataFrame for analysis
        trades_df = pd.DataFrame([{
            'entry_time': t.entry_time,
            'symbol': t.symbol,
            'pnl': t.pnl or 0,
            'direction': t.direction,
            'quantity': t.quantity,
            'strategy_tag': t.strategy_tag
        } for t in trades])
        
        # Generate time-based heatmap
        time_heatmap = self._generate_time_heatmap(trades_df)
        
        # Generate symbol performance stats
        symbol_stats = self._generate_symbol_stats(trades_df)
        
        # Generate additional insights
        insights = self._generate_heatmap_insights(trades_df, time_heatmap, symbol_stats)
        
        return {
            'time_heatmap': time_heatmap,
            'symbol_stats': symbol_stats,
            'insights': insights,
            'metadata': {
                'total_trades': len(trades),
                'date_range': {
                    'start': trades_df['entry_time'].min().isoformat() if not trades_df.empty else None,
                    'end': trades_df['entry_time'].max().isoformat() if not trades_df.empty else None
                },
                'symbols_analyzed': len(trades_df['symbol'].unique()) if not trades_df.empty else 0
            }
        }
    
    def _generate_time_heatmap(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate time-based heatmap data (hour × weekday)"""
        
        # Extract time components
        df['hour'] = df['entry_time'].dt.hour
        df['weekday'] = df['entry_time'].dt.day_name()
        df['weekday_num'] = df['entry_time'].dt.weekday  # 0=Monday, 6=Sunday
        
        # Initialize 7x24 matrix for PnL aggregation
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        hours = list(range(24))
        
        # Aggregate data
        heatmap_data = {}
        trade_counts = {}
        win_rates = {}
        
        for weekday in weekdays:
            heatmap_data[weekday] = [0.0] * 24
            trade_counts[weekday] = [0] * 24
            win_rates[weekday] = [0.0] * 24
        
        # Fill with actual data
        for _, trade in df.iterrows():
            weekday = trade['weekday']
            hour = trade['hour']
            pnl = trade['pnl']
            
            if weekday in heatmap_data:
                heatmap_data[weekday][hour] += pnl
                trade_counts[weekday][hour] += 1
        
        # Calculate win rates
        for weekday in weekdays:
            weekday_trades = df[df['weekday'] == weekday]
            for hour in hours:
                hour_trades = weekday_trades[weekday_trades['hour'] == hour]
                if len(hour_trades) > 0:
                    wins = len(hour_trades[hour_trades['pnl'] > 0])
                    win_rates[weekday][hour] = round((wins / len(hour_trades)) * 100, 1)
        
        # Calculate average PnL per trade for normalization
        avg_pnl_matrix = {}
        for weekday in weekdays:
            avg_pnl_matrix[weekday] = []
            for hour in hours:
                if trade_counts[weekday][hour] > 0:
                    avg_pnl = heatmap_data[weekday][hour] / trade_counts[weekday][hour]
                    avg_pnl_matrix[weekday].append(round(avg_pnl, 2))
                else:
                    avg_pnl_matrix[weekday].append(0.0)
        
        # Find best and worst performing time slots
        best_slots = []
        worst_slots = []
        
        for weekday in weekdays:
            for hour in hours:
                if trade_counts[weekday][hour] >= 3:  # Minimum trades for reliability
                    avg_pnl = avg_pnl_matrix[weekday][hour]
                    trade_count = trade_counts[weekday][hour]
                    
                    slot_data = {
                        'weekday': weekday,
                        'hour': hour,
                        'avg_pnl': avg_pnl,
                        'total_pnl': heatmap_data[weekday][hour],
                        'trade_count': trade_count,
                        'win_rate': win_rates[weekday][hour]
                    }
                    
                    if avg_pnl > 0:
                        best_slots.append(slot_data)
                    elif avg_pnl < 0:
                        worst_slots.append(slot_data)
        
        # Sort by average PnL
        best_slots.sort(key=lambda x: x['avg_pnl'], reverse=True)
        worst_slots.sort(key=lambda x: x['avg_pnl'])
        
        return {
            'total_pnl_matrix': heatmap_data,
            'avg_pnl_matrix': avg_pnl_matrix,
            'trade_count_matrix': trade_counts,
            'win_rate_matrix': win_rates,
            'best_time_slots': best_slots[:5],  # Top 5
            'worst_time_slots': worst_slots[:5],  # Bottom 5
            'total_trading_hours': sum(sum(1 for count in day_counts if count > 0) for day_counts in trade_counts.values())
        }
    
    def _generate_symbol_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate symbol performance statistics"""
        
        if df.empty:
            return {'symbols': [], 'summary': {}}
        
        symbol_groups = df.groupby('symbol')
        symbol_stats = []
        
        for symbol, group in symbol_groups:
            wins = group[group['pnl'] > 0]
            losses = group[group['pnl'] < 0]
            
            # Basic metrics
            total_trades = len(group)
            total_pnl = group['pnl'].sum()
            avg_pnl = group['pnl'].mean()
            win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
            
            # Risk metrics
            best_trade = group['pnl'].max()
            worst_trade = group['pnl'].min()
            
            # Profit factor
            gross_profit = wins['pnl'].sum() if len(wins) > 0 else 0
            gross_loss = abs(losses['pnl'].sum()) if len(losses) > 0 else 1
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999
            
            # Volume analysis
            total_volume = group['quantity'].sum()
            avg_volume = group['quantity'].mean()
            
            # Time analysis
            trading_days = group['entry_time'].dt.date.nunique()
            avg_trades_per_day = total_trades / trading_days if trading_days > 0 else 0
            
            # Direction bias
            long_trades = len(group[group['direction'] == 'long'])
            short_trades = len(group[group['direction'] == 'short'])
            direction_bias = 'Long' if long_trades > short_trades else 'Short' if short_trades > long_trades else 'Neutral'
            
            symbol_stats.append({
                'symbol': symbol,
                'total_trades': total_trades,
                'total_pnl': round(total_pnl, 2),
                'avg_pnl': round(avg_pnl, 2),
                'win_rate': round(win_rate, 1),
                'profit_factor': round(profit_factor, 2) if profit_factor != 999 else 999,
                'best_trade': round(best_trade, 2),
                'worst_trade': round(worst_trade, 2),
                'total_volume': round(total_volume, 0),
                'avg_volume': round(avg_volume, 1),
                'trading_days': trading_days,
                'avg_trades_per_day': round(avg_trades_per_day, 1),
                'direction_bias': direction_bias,
                'long_trades': long_trades,
                'short_trades': short_trades,
                'consistency_score': self._calculate_symbol_consistency(group)
            })
        
        # Sort by total PnL
        symbol_stats.sort(key=lambda x: x['total_pnl'], reverse=True)
        
        # Calculate summary statistics
        summary = {
            'total_symbols': len(symbol_stats),
            'profitable_symbols': len([s for s in symbol_stats if s['total_pnl'] > 0]),
            'unprofitable_symbols': len([s for s in symbol_stats if s['total_pnl'] < 0]),
            'best_symbol': symbol_stats[0]['symbol'] if symbol_stats else None,
            'worst_symbol': symbol_stats[-1]['symbol'] if symbol_stats else None,
            'most_traded_symbol': max(symbol_stats, key=lambda x: x['total_trades'])['symbol'] if symbol_stats else None,
            'avg_symbols_per_day': len(df['symbol'].unique()) / df['entry_time'].dt.date.nunique() if not df.empty else 0
        }
        
        return {
            'symbols': symbol_stats,
            'summary': summary
        }
    
    def _calculate_symbol_consistency(self, group: pd.DataFrame) -> float:
        """Calculate consistency score for a symbol (0-100)"""
        if len(group) < 5:  # Need minimum trades for meaningful consistency
            return 0.0
        
        # Calculate rolling win rate consistency
        group_sorted = group.sort_values('entry_time')
        rolling_pnl = group_sorted['pnl'].rolling(window=min(5, len(group))).mean()
        
        # Consistency = inverse of coefficient of variation
        if rolling_pnl.std() == 0:
            return 100.0
        
        cv = abs(rolling_pnl.std() / rolling_pnl.mean()) if rolling_pnl.mean() != 0 else float('inf')
        consistency = max(0, 100 - (cv * 10))  # Scale and invert
        
        return round(consistency, 1)
    
    def _generate_heatmap_insights(
        self, 
        df: pd.DataFrame, 
        time_heatmap: Dict[str, Any], 
        symbol_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate actionable insights from heatmap data"""
        
        insights = {
            'time_insights': [],
            'symbol_insights': [],
            'recommendations': []
        }
        
        if df.empty:
            return insights
        
        # Time-based insights
        best_slots = time_heatmap.get('best_time_slots', [])
        worst_slots = time_heatmap.get('worst_time_slots', [])
        
        if best_slots:
            best_slot = best_slots[0]
            insights['time_insights'].append({
                'type': 'best_time',
                'message': f"Peak performance: {best_slot['weekday']}s at {best_slot['hour']:02d}:00 "
                          f"(Avg: ${best_slot['avg_pnl']:.2f}, Win Rate: {best_slot['win_rate']:.1f}%)",
                'data': best_slot
            })
        
        if worst_slots:
            worst_slot = worst_slots[0]
            insights['time_insights'].append({
                'type': 'worst_time',
                'message': f"Avoid: {worst_slot['weekday']}s at {worst_slot['hour']:02d}:00 "
                          f"(Avg: ${worst_slot['avg_pnl']:.2f}, Win Rate: {worst_slot['win_rate']:.1f}%)",
                'data': worst_slot
            })
        
        # Symbol-based insights
        symbols = symbol_stats.get('symbols', [])
        if symbols:
            best_symbol = symbols[0]
            if best_symbol['total_pnl'] > 0:
                insights['symbol_insights'].append({
                    'type': 'best_symbol',
                    'message': f"Top performer: {best_symbol['symbol']} "
                              f"(${best_symbol['total_pnl']:.2f} across {best_symbol['total_trades']} trades)",
                    'data': best_symbol
                })
            
            worst_symbol = symbols[-1]
            if worst_symbol['total_pnl'] < 0:
                insights['symbol_insights'].append({
                    'type': 'worst_symbol',
                    'message': f"Underperformer: {worst_symbol['symbol']} "
                              f"(${worst_symbol['total_pnl']:.2f} loss across {worst_symbol['total_trades']} trades)",
                    'data': worst_symbol
                })
        
        # Generate recommendations
        insights['recommendations'] = self._generate_recommendations(df, time_heatmap, symbol_stats)
        
        return insights
    
    def _generate_recommendations(
        self, 
        df: pd.DataFrame, 
        time_heatmap: Dict[str, Any], 
        symbol_stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable trading recommendations"""
        
        recommendations = []
        
        # Time-based recommendations
        best_slots = time_heatmap.get('best_time_slots', [])
        worst_slots = time_heatmap.get('worst_time_slots', [])
        
        if best_slots:
            focus_hours = [f"{slot['weekday']} {slot['hour']:02d}:00" for slot in best_slots[:3]]
            recommendations.append({
                'type': 'focus_times',
                'priority': 'high',
                'title': 'Focus on High-Performance Hours',
                'description': f"Concentrate trading during: {', '.join(focus_hours)}",
                'expected_impact': 'Increase average PnL per trade by focusing on proven time slots'
            })
        
        if worst_slots:
            avoid_hours = [f"{slot['weekday']} {slot['hour']:02d}:00" for slot in worst_slots[:3]]
            recommendations.append({
                'type': 'avoid_times',
                'priority': 'medium',
                'title': 'Avoid Underperforming Hours',
                'description': f"Consider reducing activity during: {', '.join(avoid_hours)}",
                'expected_impact': 'Reduce losses by avoiding historically poor time slots'
            })
        
        # Symbol-based recommendations
        symbols = symbol_stats.get('symbols', [])
        profitable_symbols = [s for s in symbols if s['total_pnl'] > 0 and s['total_trades'] >= 5]
        unprofitable_symbols = [s for s in symbols if s['total_pnl'] < -100 and s['total_trades'] >= 5]
        
        if profitable_symbols:
            top_symbols = [s['symbol'] for s in profitable_symbols[:3]]
            recommendations.append({
                'type': 'focus_symbols',
                'priority': 'high',
                'title': 'Double Down on Winning Symbols',
                'description': f"Increase position sizing or frequency on: {', '.join(top_symbols)}",
                'expected_impact': 'Scale profitable patterns for higher returns'
            })
        
        if unprofitable_symbols:
            problem_symbols = [s['symbol'] for s in unprofitable_symbols[:2]]
            recommendations.append({
                'type': 'review_symbols',
                'priority': 'high',
                'title': 'Review Underperforming Symbols',
                'description': f"Analyze or reduce exposure to: {', '.join(problem_symbols)}",
                'expected_impact': 'Stop bleeding money on consistently losing instruments'
            })
        
        # Volume-based recommendations
        if not df.empty:
            volume_analysis = df.groupby('symbol')['quantity'].agg(['mean', 'std', 'count'])
            high_volume_symbols = volume_analysis[volume_analysis['mean'] > volume_analysis['mean'].quantile(0.8)]
            
            if not high_volume_symbols.empty:
                recommendations.append({
                    'type': 'position_sizing',
                    'priority': 'medium',
                    'title': 'Optimize Position Sizing',
                    'description': 'Review position sizes on high-volume symbols for risk management',
                    'expected_impact': 'Better risk-adjusted returns through proper sizing'
                })
        
        return recommendations
    
    def _empty_heatmap_response(self) -> Dict[str, Any]:
        """Return empty response when no data available"""
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        return {
            'time_heatmap': {
                'total_pnl_matrix': {day: [0.0] * 24 for day in weekdays},
                'avg_pnl_matrix': {day: [0.0] * 24 for day in weekdays},
                'trade_count_matrix': {day: [0] * 24 for day in weekdays},
                'win_rate_matrix': {day: [0.0] * 24 for day in weekdays},
                'best_time_slots': [],
                'worst_time_slots': [],
                'total_trading_hours': 0
            },
            'symbol_stats': {
                'symbols': [],
                'summary': {
                    'total_symbols': 0,
                    'profitable_symbols': 0,
                    'unprofitable_symbols': 0,
                    'best_symbol': None,
                    'worst_symbol': None,
                    'most_traded_symbol': None,
                    'avg_symbols_per_day': 0
                }
            },
            'insights': {
                'time_insights': [],
                'symbol_insights': [],
                'recommendations': []
            },
            'metadata': {
                'total_trades': 0,
                'date_range': {'start': None, 'end': None},
                'symbols_analyzed': 0
            }
        }
