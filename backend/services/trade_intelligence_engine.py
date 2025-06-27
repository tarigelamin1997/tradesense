
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
from backend.core.db.session import SessionLocal
import numpy as np

logger = logging.getLogger(__name__)

class TradeIntelligenceEngine:
    """Advanced AI-powered trade analysis and prediction engine"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.model_weights = self._initialize_model_weights()
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        }
    
    def _initialize_model_weights(self) -> Dict[str, float]:
        """Initialize ML model weights for trade scoring"""
        return {
            'market_regime_alignment': 0.25,
            'historical_performance': 0.20,
            'execution_timing': 0.15,
            'position_sizing': 0.15,
            'strategy_consistency': 0.15,
            'emotional_state': 0.10
        }
    
    def score_trade_pre_execution(self, user_id: str, trade_data: Dict) -> Dict[str, Any]:
        """Score a trade before execution to predict success probability"""
        try:
            score_components = {}
            
            # 1. Market Regime Analysis
            market_score = self._analyze_market_regime_fit(trade_data)
            score_components['market_regime'] = market_score
            
            # 2. Historical Performance in Similar Conditions
            historical_score = self._analyze_historical_performance(user_id, trade_data)
            score_components['historical_performance'] = historical_score
            
            # 3. Execution Timing Quality
            timing_score = self._analyze_execution_timing(trade_data)
            score_components['execution_timing'] = timing_score
            
            # 4. Position Sizing Appropriateness
            sizing_score = self._analyze_position_sizing(user_id, trade_data)
            score_components['position_sizing'] = sizing_score
            
            # 5. Strategy Consistency
            consistency_score = self._analyze_strategy_consistency(user_id, trade_data)
            score_components['strategy_consistency'] = consistency_score
            
            # 6. Emotional State Factor
            emotional_score = self._analyze_emotional_state(user_id, trade_data)
            score_components['emotional_state'] = emotional_score
            
            # Calculate weighted final score
            final_score = sum(
                score_components[component] * self.model_weights[component.replace('_', '_')]
                for component in score_components
            )
            
            # Generate risk assessment
            risk_level = self._determine_risk_level(final_score, score_components)
            
            # Generate recommendations
            recommendations = self._generate_trade_recommendations(score_components, trade_data)
            
            return {
                'overall_score': round(final_score * 100, 1),
                'risk_level': risk_level,
                'score_components': score_components,
                'recommendations': recommendations,
                'confidence_interval': self._calculate_confidence_interval(score_components),
                'expected_outcome': self._predict_trade_outcome(final_score, trade_data)
            }
            
        except Exception as e:
            logger.error(f"Error scoring trade: {str(e)}")
            return self._fallback_score()
    
    def _analyze_market_regime_fit(self, trade_data: Dict) -> float:
        """Analyze how well the trade fits current market regime"""
        try:
            # Get current market regime (mock implementation)
            current_regime = self._get_current_market_regime()
            
            strategy = trade_data.get('strategy', '').lower()
            trade_type = trade_data.get('side', '').lower()
            
            # Strategy-regime alignment scoring
            regime_alignment = {
                'bull': {
                    'momentum': 0.9, 'breakout': 0.8, 'trend_following': 0.85,
                    'mean_reversion': 0.3, 'contrarian': 0.2
                },
                'bear': {
                    'momentum': 0.7, 'breakout': 0.6, 'trend_following': 0.7,
                    'mean_reversion': 0.8, 'contrarian': 0.9
                },
                'sideways': {
                    'momentum': 0.4, 'breakout': 0.3, 'trend_following': 0.3,
                    'mean_reversion': 0.9, 'range_trading': 0.95
                }
            }
            
            regime = current_regime.get('type', 'sideways')
            base_score = regime_alignment.get(regime, {}).get(strategy, 0.5)
            
            # Adjust for volatility
            volatility_adjustment = self._get_volatility_adjustment(current_regime, trade_data)
            
            return min(1.0, base_score + volatility_adjustment)
            
        except Exception as e:
            logger.error(f"Error analyzing market regime fit: {str(e)}")
            return 0.5
    
    def _analyze_historical_performance(self, user_id: str, trade_data: Dict) -> float:
        """Analyze user's historical performance in similar setups"""
        try:
            # Get similar historical trades
            similar_trades = self._find_similar_trades(user_id, trade_data)
            
            if not similar_trades:
                return 0.5  # Neutral score for no history
            
            # Calculate win rate and average return
            wins = sum(1 for trade in similar_trades if trade.pnl > 0)
            win_rate = wins / len(similar_trades)
            
            avg_return = sum(trade.pnl for trade in similar_trades) / len(similar_trades)
            avg_return_pct = avg_return / (sum(abs(trade.pnl) for trade in similar_trades) / len(similar_trades))
            
            # Weight recent performance more heavily
            recent_trades = [t for t in similar_trades if t.entry_time > datetime.now() - timedelta(days=90)]
            if recent_trades:
                recent_win_rate = sum(1 for t in recent_trades if t.pnl > 0) / len(recent_trades)
                win_rate = (win_rate * 0.4) + (recent_win_rate * 0.6)
            
            # Combine win rate and profitability
            performance_score = (win_rate * 0.6) + (min(1.0, max(0.0, avg_return_pct + 0.5)) * 0.4)
            
            return performance_score
            
        except Exception as e:
            logger.error(f"Error analyzing historical performance: {str(e)}")
            return 0.5
    
    def _analyze_execution_timing(self, trade_data: Dict) -> float:
        """Analyze the timing quality of the trade execution"""
        try:
            current_time = datetime.now()
            market_open = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = current_time.replace(hour=16, minute=0, second=0, microsecond=0)
            
            # Time-based scoring
            if market_open <= current_time <= market_open + timedelta(hours=1):
                # Opening hour - high volatility, good for breakouts
                time_score = 0.8 if 'breakout' in trade_data.get('strategy', '').lower() else 0.6
            elif market_close - timedelta(hours=1) <= current_time <= market_close:
                # Closing hour - institutional activity
                time_score = 0.7
            elif market_open + timedelta(hours=2) <= current_time <= market_close - timedelta(hours=2):
                # Mid-day - lower volatility, good for mean reversion
                time_score = 0.8 if 'mean_reversion' in trade_data.get('strategy', '').lower() else 0.5
            else:
                # After hours or pre-market
                time_score = 0.3
            
            # Adjust for day of week
            weekday = current_time.weekday()
            if weekday == 0:  # Monday
                time_score *= 1.1  # Often good momentum days
            elif weekday == 4:  # Friday
                time_score *= 0.9  # Often choppy
            
            return min(1.0, time_score)
            
        except Exception as e:
            logger.error(f"Error analyzing execution timing: {str(e)}")
            return 0.5
    
    def _analyze_position_sizing(self, user_id: str, trade_data: Dict) -> float:
        """Analyze if position size is appropriate for user's account and risk profile"""
        try:
            # Get user's recent position sizes
            recent_trades = self.db.query(Trade).filter(
                Trade.user_id == user_id
            ).order_by(desc(Trade.entry_time)).limit(20).all()
            
            if not recent_trades:
                return 0.5
            
            current_size = abs(trade_data.get('quantity', 0))
            recent_sizes = [abs(t.quantity) for t in recent_trades]
            avg_size = sum(recent_sizes) / len(recent_sizes)
            
            # Calculate position size consistency
            size_ratio = current_size / avg_size if avg_size > 0 else 1.0
            
            # Optimal range is 0.5x to 2x average size
            if 0.5 <= size_ratio <= 2.0:
                consistency_score = 1.0 - abs(size_ratio - 1.0) * 0.5
            else:
                consistency_score = max(0.1, 0.5 - abs(size_ratio - 1.0) * 0.3)
            
            # Factor in strategy type - some strategies warrant larger positions
            strategy = trade_data.get('strategy', '').lower()
            if 'high_conviction' in strategy or 'breakout' in strategy:
                if size_ratio > 1.0:
                    consistency_score *= 1.2  # Reward larger size for high conviction
            
            return min(1.0, consistency_score)
            
        except Exception as e:
            logger.error(f"Error analyzing position sizing: {str(e)}")
            return 0.5
    
    def _analyze_strategy_consistency(self, user_id: str, trade_data: Dict) -> float:
        """Analyze if trade is consistent with user's successful strategies"""
        try:
            # Get user's strategy performance
            strategy_performance = self._get_strategy_performance(user_id)
            
            current_strategy = trade_data.get('strategy', '').lower()
            
            if current_strategy in strategy_performance:
                perf = strategy_performance[current_strategy]
                win_rate = perf['win_rate']
                avg_return = perf['avg_return']
                trade_count = perf['trade_count']
                
                # Weight by number of trades (more data = more confidence)
                confidence_weight = min(1.0, trade_count / 20)
                
                # Combine win rate and profitability
                strategy_score = (win_rate * 0.7) + (min(1.0, max(0.0, avg_return + 0.5)) * 0.3)
                
                return strategy_score * confidence_weight + 0.5 * (1 - confidence_weight)
            
            return 0.5  # Neutral for new strategy
            
        except Exception as e:
            logger.error(f"Error analyzing strategy consistency: {str(e)}")
            return 0.5
    
    def _analyze_emotional_state(self, user_id: str, trade_data: Dict) -> float:
        """Analyze user's likely emotional state based on recent performance"""
        try:
            # Get last 10 trades
            recent_trades = self.db.query(Trade).filter(
                Trade.user_id == user_id
            ).order_by(desc(Trade.entry_time)).limit(10).all()
            
            if not recent_trades:
                return 0.7  # Slightly positive for new users
            
            # Calculate recent performance metrics
            recent_pnl = [t.pnl for t in recent_trades[:5]]  # Last 5 trades
            win_streak = 0
            loss_streak = 0
            
            for trade in recent_trades:
                if trade.pnl > 0:
                    win_streak += 1
                    break
                else:
                    loss_streak += 1
            
            # Emotional state scoring
            emotional_score = 0.7  # Base neutral state
            
            # Adjust for streaks
            if win_streak >= 3:
                emotional_score = 0.4  # Possible overconfidence
            elif loss_streak >= 3:
                emotional_score = 0.3  # Possible revenge trading
            elif loss_streak == 1 or loss_streak == 2:
                emotional_score = 0.8  # Likely focused and careful
            
            # Adjust for recent P&L volatility
            if len(recent_pnl) >= 3:
                pnl_std = np.std(recent_pnl)
                pnl_mean = np.mean(recent_pnl)
                
                if pnl_std > abs(pnl_mean) * 2:  # High volatility
                    emotional_score *= 0.8  # Potentially unstable state
            
            return emotional_score
            
        except Exception as e:
            logger.error(f"Error analyzing emotional state: {str(e)}")
            return 0.5
    
    def _generate_trade_recommendations(self, score_components: Dict, trade_data: Dict) -> List[str]:
        """Generate actionable recommendations based on score components"""
        recommendations = []
        
        # Market regime recommendations
        if score_components.get('market_regime', 0.5) < 0.4:
            recommendations.append("⚠️ Current market regime doesn't favor this strategy - consider waiting")
        
        # Historical performance recommendations
        if score_components.get('historical_performance', 0.5) < 0.3:
            recommendations.append("📊 Your historical performance with this setup is poor - consider paper trading first")
        elif score_components.get('historical_performance', 0.5) > 0.8:
            recommendations.append("✅ Strong historical performance with this setup - good execution")
        
        # Timing recommendations
        if score_components.get('execution_timing', 0.5) < 0.4:
            recommendations.append("⏰ Timing could be better - consider waiting for optimal market hours")
        
        # Position size recommendations
        if score_components.get('position_sizing', 0.5) < 0.4:
            recommendations.append("📏 Position size seems inappropriate - consider adjusting to your typical range")
        
        # Emotional state recommendations
        if score_components.get('emotional_state', 0.5) < 0.4:
            recommendations.append("🧠 Your emotional state may be affecting judgment - take a step back")
        
        if not recommendations:
            recommendations.append("✅ Trade setup looks solid - execute with confidence")
        
        return recommendations
    
    def _determine_risk_level(self, final_score: float, components: Dict) -> str:
        """Determine overall risk level for the trade"""
        if final_score >= 0.7:
            return "Low"
        elif final_score >= 0.5:
            return "Medium" 
        else:
            return "High"
    
    def _calculate_confidence_interval(self, components: Dict) -> Tuple[float, float]:
        """Calculate confidence interval for the prediction"""
        # Simple confidence interval based on component variance
        scores = list(components.values())
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        
        lower = max(0.0, mean_score - 1.96 * std_dev)
        upper = min(1.0, mean_score + 1.96 * std_dev)
        
        return (round(lower * 100, 1), round(upper * 100, 1))
    
    def _predict_trade_outcome(self, score: float, trade_data: Dict) -> Dict[str, Any]:
        """Predict likely trade outcome"""
        # Simple prediction model
        win_probability = score
        
        # Estimate potential return based on historical data
        strategy = trade_data.get('strategy', '').lower()
        expected_return = self._get_strategy_expected_return(strategy)
        
        return {
            'win_probability': round(win_probability * 100, 1),
            'expected_return_pct': round(expected_return * 100, 2),
            'risk_reward_ratio': round(abs(expected_return) / max(0.01, 1 - win_probability), 2)
        }
    
    # Helper methods (mock implementations for now)
    def _get_current_market_regime(self) -> Dict:
        """Get current market regime data"""
        return {'type': 'bull', 'confidence': 0.7, 'volatility': 'medium'}
    
    def _get_volatility_adjustment(self, regime: Dict, trade_data: Dict) -> float:
        """Get volatility-based adjustment to score"""
        return 0.0  # Placeholder
    
    def _find_similar_trades(self, user_id: str, trade_data: Dict) -> List[Trade]:
        """Find historically similar trades"""
        symbol = trade_data.get('symbol', '')
        strategy = trade_data.get('strategy', '')
        
        return self.db.query(Trade).filter(
            and_(
                Trade.user_id == user_id,
                Trade.symbol == symbol,
                Trade.tags.contains([strategy]) if strategy else True
            )
        ).limit(50).all()
    
    def _get_strategy_performance(self, user_id: str) -> Dict:
        """Get performance by strategy for user"""
        trades = self.db.query(Trade).filter(Trade.user_id == user_id).all()
        strategy_stats = defaultdict(lambda: {'wins': 0, 'total': 0, 'total_pnl': 0})
        
        for trade in trades:
            if trade.tags:
                for tag in trade.tags:
                    strategy_stats[tag.lower()]['total'] += 1
                    strategy_stats[tag.lower()]['total_pnl'] += trade.pnl
                    if trade.pnl > 0:
                        strategy_stats[tag.lower()]['wins'] += 1
        
        result = {}
        for strategy, stats in strategy_stats.items():
            if stats['total'] >= 3:  # Only include strategies with enough trades
                result[strategy] = {
                    'win_rate': stats['wins'] / stats['total'],
                    'avg_return': stats['total_pnl'] / stats['total'],
                    'trade_count': stats['total']
                }
        
        return result
    
    def _get_strategy_expected_return(self, strategy: str) -> float:
        """Get expected return for strategy type"""
        strategy_returns = {
            'momentum': 0.02,
            'breakout': 0.03,
            'mean_reversion': 0.015,
            'trend_following': 0.025,
            'contrarian': 0.01
        }
        return strategy_returns.get(strategy, 0.015)
    
    def _fallback_score(self) -> Dict[str, Any]:
        """Fallback scoring when analysis fails"""
        return {
            'overall_score': 50.0,
            'risk_level': 'Medium',
            'score_components': {},
            'recommendations': ['⚠️ Unable to analyze trade - proceed with caution'],
            'confidence_interval': (40.0, 60.0),
            'expected_outcome': {
                'win_probability': 50.0,
                'expected_return_pct': 1.5,
                'risk_reward_ratio': 1.0
            }
        }
    
    def __del__(self):
        """Cleanup database session"""
        if hasattr(self, 'db'):
            self.db.close()
