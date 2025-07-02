"""
Advanced Trade Intelligence Engine for TradeSense
Provides real-time trade scoring, risk assessment, and strategy recommendations
"""
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from backend.models.trade import Trade
from backend.models.milestone import Milestone
from backend.core.db.session import get_db
import numpy as np

logger = logging.getLogger(__name__)

class TradeIntelligenceEngine:
    """Advanced AI-powered trade analysis and recommendation engine"""
    
    def __init__(self):
        self.market_regimes = {
            'bull': {'momentum_weight': 0.8, 'mean_reversion_weight': 0.2},
            'bear': {'momentum_weight': 0.3, 'mean_reversion_weight': 0.7},
            'sideways': {'momentum_weight': 0.4, 'mean_reversion_weight': 0.6}
        }
    
    def analyze_trade_quality(self, trade_data: Dict) -> Dict[str, Any]:
        """Comprehensive trade quality analysis"""
        try:
            # Extract trade metrics
            entry_price = trade_data.get('entry_price', 0)
            exit_price = trade_data.get('exit_price', 0)
            quantity = trade_data.get('quantity', 0)
            symbol = trade_data.get('symbol', '')
            strategy = trade_data.get('strategy', 'unknown')
            confidence = trade_data.get('confidence_level', 5)
            
            # Calculate basic metrics
            pnl = (exit_price - entry_price) * quantity
            pnl_percentage = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            
            # Risk-reward analysis
            risk_reward_ratio = self._calculate_risk_reward(trade_data)
            
            # Execution quality score
            execution_score = self._analyze_execution_quality(trade_data)
            
            # Market timing analysis
            timing_score = self._analyze_market_timing(trade_data)
            
            # Strategy alignment score
            strategy_score = self._analyze_strategy_alignment(trade_data)
            
            # Overall trade score (0-100)
            overall_score = self._calculate_overall_score(
                execution_score, timing_score, strategy_score, pnl_percentage
            )
            
            # Generate insights and recommendations
            insights = self._generate_trade_insights(trade_data, overall_score)
            
            return {
                'overall_score': overall_score,
                'pnl': pnl,
                'pnl_percentage': pnl_percentage,
                'risk_reward_ratio': risk_reward_ratio,
                'execution_score': execution_score,
                'timing_score': timing_score,
                'strategy_score': strategy_score,
                'insights': insights,
                'recommendations': self._generate_recommendations(trade_data, overall_score),
                'market_context': self._get_market_context_at_trade_time(trade_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trade quality: {e}")
            return {'error': str(e)}
    
    def get_real_time_trade_score(self, trade_setup: Dict) -> Dict[str, Any]:
        """Real-time scoring of potential trade setups"""
        try:
            symbol = trade_setup.get('symbol', '')
            strategy = trade_setup.get('strategy', '')
            entry_price = trade_setup.get('entry_price', 0)
            stop_loss = trade_setup.get('stop_loss', 0)
            take_profit = trade_setup.get('take_profit', 0)
            
            # Market regime analysis
            current_regime = self._get_current_market_regime()
            
            # Strategy-regime compatibility
            regime_compatibility = self._assess_strategy_regime_fit(strategy, current_regime)
            
            # Risk assessment
            risk_assessment = self._assess_trade_risk(trade_setup)
            
            # Probability calculation
            win_probability = self._calculate_win_probability(trade_setup)
            
            # Expected value calculation
            expected_value = self._calculate_expected_value(trade_setup, win_probability)
            
            # Real-time score (0-100)
            real_time_score = self._calculate_real_time_score(
                regime_compatibility, risk_assessment, win_probability, expected_value
            )
            
            return {
                'real_time_score': real_time_score,
                'win_probability': win_probability,
                'expected_value': expected_value,
                'risk_level': risk_assessment['risk_level'],
                'market_regime': current_regime,
                'regime_compatibility': regime_compatibility,
                'recommendations': self._generate_setup_recommendations(trade_setup, real_time_score),
                'alerts': self._generate_trade_alerts(trade_setup, real_time_score)
            }
            
        except Exception as e:
            logger.error(f"Error calculating real-time trade score: {e}")
            return {'error': str(e)}
    
    def analyze_trading_patterns(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Analyze user's trading patterns and behavioral insights"""
        try:
            # Get recent trades
            db = get_db()
            trades = db.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.entry_time >= datetime.now() - timedelta(days=days)
            ).all()
            db.close()
            
            if not trades:
                return {'error': 'No trades found for analysis'}
            
            # Convert to DataFrame for analysis
            trade_data = []
            for trade in trades:
                trade_data.append({
                    'entry_time': trade.entry_time,
                    'exit_time': trade.exit_time,
                    'symbol': trade.symbol,
                    'strategy': trade.strategy,
                    'pnl': trade.pnl,
                    'confidence_level': trade.confidence_level,
                    'emotional_state': trade.emotional_state
                })
            
            df = pd.DataFrame(trade_data)
            
            # Pattern analysis
            patterns = {
                'time_patterns': self._analyze_time_patterns(df),
                'strategy_performance': self._analyze_strategy_performance(df),
                'emotional_patterns': self._analyze_emotional_patterns(df),
                'streak_patterns': self._analyze_streak_patterns(df),
                'confidence_calibration': self._analyze_confidence_calibration(df)
            }
            
            # Generate insights
            insights = self._generate_pattern_insights(patterns)
            
            # Performance predictions
            predictions = self._generate_performance_predictions(patterns)
            
            return {
                'patterns': patterns,
                'insights': insights,
                'predictions': predictions,
                'optimization_suggestions': self._generate_optimization_suggestions(patterns)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trading patterns: {e}")
            return {'error': str(e)}
    
    def _calculate_risk_reward(self, trade_data: Dict) -> float:
        """Calculate risk-reward ratio"""
        entry_price = trade_data.get('entry_price', 0)
        exit_price = trade_data.get('exit_price', 0)
        stop_loss = trade_data.get('stop_loss', entry_price * 0.98)  # Default 2% stop
        
        if entry_price == 0:
            return 0
        
        risk = abs(entry_price - stop_loss)
        reward = abs(exit_price - entry_price)
        
        return reward / risk if risk > 0 else 0
    
    def _analyze_execution_quality(self, trade_data: Dict) -> float:
        """Analyze trade execution quality (0-100)"""
        # Simplified execution analysis
        slippage = trade_data.get('slippage', 0)
        timing_score = 85 - (abs(slippage) * 1000)  # Penalize slippage
        
        return max(0, min(100, timing_score))
    
    def _analyze_market_timing(self, trade_data: Dict) -> float:
        """Analyze market timing quality (0-100)"""
        # Simplified timing analysis based on market conditions
        market_volatility = trade_data.get('market_volatility', 0.5)
        
        # Better timing in lower volatility for most strategies
        timing_score = 100 - (market_volatility * 50)
        
        return max(0, min(100, timing_score))
    
    def _analyze_strategy_alignment(self, trade_data: Dict) -> float:
        """Analyze how well trade aligns with stated strategy (0-100)"""
        strategy = trade_data.get('strategy', '').lower()
        pnl_percentage = trade_data.get('pnl_percentage', 0)
        
        # Strategy-specific scoring
        if 'momentum' in strategy:
            # Momentum strategies should capture larger moves
            return min(100, 70 + abs(pnl_percentage) * 5)
        elif 'mean_reversion' in strategy:
            # Mean reversion should be quick and precise
            return min(100, 80 + (10 if abs(pnl_percentage) < 2 else 0))
        else:
            return 75  # Default score
    
    def _calculate_overall_score(self, execution: float, timing: float, strategy: float, pnl_pct: float) -> float:
        """Calculate overall trade score"""
        # Weighted combination of factors
        score = (execution * 0.3 + timing * 0.3 + strategy * 0.2) * 0.8
        
        # Bonus for profitable trades
        if pnl_pct > 0:
            score += min(20, pnl_pct * 2)
        else:
            score += max(-20, pnl_pct * 1.5)
        
        return max(0, min(100, score))
    
    def _generate_trade_insights(self, trade_data: Dict, score: float) -> List[str]:
        """Generate specific insights about the trade"""
        insights = []
        
        if score >= 80:
            insights.append("🎯 Excellent trade execution - strategy and timing aligned perfectly")
        elif score >= 60:
            insights.append("✅ Good trade overall with room for minor improvements")
        elif score >= 40:
            insights.append("⚠️ Mixed results - review strategy alignment and timing")
        else:
            insights.append("🔴 Poor trade execution - significant improvement needed")
        
        # Add specific insights based on trade characteristics
        risk_reward = self._calculate_risk_reward(trade_data)
        if risk_reward > 2:
            insights.append("💎 Excellent risk-reward ratio maintained")
        elif risk_reward < 1:
            insights.append("⚠️ Poor risk-reward ratio - consider tighter stops or larger targets")
        
        return insights
    
    def _generate_recommendations(self, trade_data: Dict, score: float) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if score < 60:
            recommendations.append("📚 Review strategy rules and market conditions before next trade")
            recommendations.append("⏰ Consider better entry timing based on market regime")
        
        if self._calculate_risk_reward(trade_data) < 1.5:
            recommendations.append("🎯 Improve target selection for better risk-reward ratios")
        
        recommendations.append("📊 Log emotional state and market conditions for pattern analysis")
        
        return recommendations
    
    def _get_current_market_regime(self) -> Dict[str, Any]:
        """Get current market regime analysis"""
        # Simplified market regime detection
        return {
            'type': 'bull',  # This would be determined by real market analysis
            'confidence': 0.75,
            'volatility': 'medium'
        }
    
    def _assess_strategy_regime_fit(self, strategy: str, regime: Dict) -> float:
        """Assess how well strategy fits current market regime (0-1)"""
        regime_type = regime.get('type', 'sideways')
        
        strategy_fits = {
            'bull': {'momentum': 0.9, 'breakout': 0.8, 'mean_reversion': 0.3},
            'bear': {'momentum': 0.4, 'breakout': 0.3, 'mean_reversion': 0.8},
            'sideways': {'momentum': 0.5, 'breakout': 0.4, 'mean_reversion': 0.9}
        }
        
        return strategy_fits.get(regime_type, {}).get(strategy.lower(), 0.5)
    
    def _assess_trade_risk(self, trade_setup: Dict) -> Dict[str, Any]:
        """Assess overall trade risk"""
        entry_price = trade_setup.get('entry_price', 0)
        stop_loss = trade_setup.get('stop_loss', 0)
        position_size = trade_setup.get('position_size', 0)
        
        risk_amount = abs(entry_price - stop_loss) * position_size if entry_price > 0 else 0
        risk_percentage = (risk_amount / (entry_price * position_size)) * 100 if entry_price > 0 else 0
        
        if risk_percentage <= 1:
            risk_level = 'low'
        elif risk_percentage <= 2:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        return {
            'risk_amount': risk_amount,
            'risk_percentage': risk_percentage,
            'risk_level': risk_level
        }
    
    def _calculate_win_probability(self, trade_setup: Dict) -> float:
        """Calculate probability of winning trade"""
        # Simplified probability calculation
        strategy = trade_setup.get('strategy', '').lower()
        
        base_probabilities = {
            'momentum': 0.55,
            'mean_reversion': 0.60,
            'breakout': 0.45,
            'scalping': 0.65
        }
        
        return base_probabilities.get(strategy, 0.50)
    
    def _calculate_expected_value(self, trade_setup: Dict, win_prob: float) -> float:
        """Calculate expected value of trade"""
        entry_price = trade_setup.get('entry_price', 0)
        stop_loss = trade_setup.get('stop_loss', 0)
        take_profit = trade_setup.get('take_profit', 0)
        
        if entry_price == 0:
            return 0
        
        win_amount = abs(take_profit - entry_price)
        loss_amount = abs(entry_price - stop_loss)
        
        expected_value = (win_prob * win_amount) - ((1 - win_prob) * loss_amount)
        
        return expected_value / entry_price * 100  # Return as percentage
    
    def _calculate_real_time_score(self, regime_fit: float, risk_assessment: Dict, 
                                  win_prob: float, expected_value: float) -> float:
        """Calculate real-time trade setup score"""
        # Weighted scoring
        regime_score = regime_fit * 30
        risk_score = (1 - min(risk_assessment['risk_percentage'] / 3, 1)) * 25
        probability_score = win_prob * 25
        ev_score = max(0, min(expected_value / 2, 1)) * 20
        
        return regime_score + risk_score + probability_score + ev_score
    
    def _generate_setup_recommendations(self, trade_setup: Dict, score: float) -> List[str]:
        """Generate recommendations for trade setup"""
        recommendations = []
        
        if score >= 75:
            recommendations.append("🚀 High-quality setup - consider taking this trade")
        elif score >= 50:
            recommendations.append("⚖️ Moderate setup - ensure proper risk management")
        else:
            recommendations.append("⛔ Low-quality setup - consider waiting for better opportunity")
        
        return recommendations
    
    def _generate_trade_alerts(self, trade_setup: Dict, score: float) -> List[str]:
        """Generate alerts for trade setup"""
        alerts = []
        
        risk_pct = self._assess_trade_risk(trade_setup)['risk_percentage']
        if risk_pct > 2:
            alerts.append("⚠️ HIGH RISK: Position size may be too large")
        
        if score < 30:
            alerts.append("🔴 POOR SETUP: Multiple factors against this trade")
        
        return alerts
    
    def _get_market_context_at_trade_time(self, trade_data: Dict) -> Dict[str, Any]:
        """Get market context when trade was executed"""
        return {
            'market_regime': 'bull',  # This would be historical regime data
            'volatility': 'medium',
            'sector_performance': 'positive',
            'economic_events': []
        }
    
    def _analyze_time_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze time-based trading patterns"""
        if df.empty:
            return {}
        
        # Add time-based features
        df['hour'] = pd.to_datetime(df['entry_time']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['entry_time']).dt.dayofweek
        
        # Performance by hour
        hourly_performance = df.groupby('hour')['pnl'].agg(['mean', 'count']).to_dict()
        
        # Performance by day of week
        daily_performance = df.groupby('day_of_week')['pnl'].agg(['mean', 'count']).to_dict()
        
        return {
            'best_hours': hourly_performance,
            'best_days': daily_performance
        }
    
    def _analyze_strategy_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by strategy"""
        if df.empty or 'strategy' not in df.columns:
            return {}
        
        strategy_stats = df.groupby('strategy')['pnl'].agg([
            'count', 'mean', 'sum', 
            lambda x: (x > 0).sum() / len(x)  # Win rate
        ]).to_dict()
        
        return strategy_stats
    
    def _analyze_emotional_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze emotional state patterns"""
        if df.empty or 'emotional_state' not in df.columns:
            return {}
        
        emotional_performance = df.groupby('emotional_state')['pnl'].agg([
            'count', 'mean', lambda x: (x > 0).sum() / len(x)
        ]).to_dict()
        
        return emotional_performance
    
    def _analyze_streak_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze win/loss streak patterns"""
        if df.empty:
            return {}
        
        df = df.sort_values('entry_time')
        df['is_winner'] = df['pnl'] > 0
        
        # Calculate streaks
        df['streak_id'] = (df['is_winner'] != df['is_winner'].shift()).cumsum()
        streaks = df.groupby('streak_id').agg({
            'is_winner': 'first',
            'pnl': ['count', 'sum']
        })
        
        return {
            'max_win_streak': streaks[streaks[('is_winner', 'first')]]['pnl']['count'].max(),
            'max_loss_streak': streaks[~streaks[('is_winner', 'first')]]['pnl']['count'].max()
        }
    
    def _analyze_confidence_calibration(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze confidence vs actual performance"""
        if df.empty or 'confidence_level' not in df.columns:
            return {}
        
        confidence_performance = df.groupby('confidence_level')['pnl'].agg([
            'count', 'mean', lambda x: (x > 0).sum() / len(x)
        ]).to_dict()
        
        return confidence_performance
    
    def _generate_pattern_insights(self, patterns: Dict) -> List[str]:
        """Generate insights from pattern analysis"""
        insights = []
        
        # Add pattern-based insights
        insights.append("📊 Pattern analysis completed - review specific metrics for optimization")
        
        return insights
    
    def _generate_performance_predictions(self, patterns: Dict) -> Dict[str, Any]:
        """Generate performance predictions based on patterns"""
        return {
            'predicted_win_rate': 0.65,  # This would be calculated from patterns
            'optimal_strategy': 'momentum',
            'best_trading_hours': [10, 11, 14, 15]
        }
    
    def _generate_optimization_suggestions(self, patterns: Dict) -> List[str]:
        """Generate optimization suggestions"""
        suggestions = [
            "🎯 Focus on your highest-performing strategies during optimal hours",
            "📈 Consider position sizing adjustments based on confidence levels",
            "🧠 Monitor emotional state before entering trades"
        ]
        
        return suggestions
