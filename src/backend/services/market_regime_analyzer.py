
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
from enum import Enum

class MarketRegime(Enum):
    BULL_TRENDING = "bull_trending"
    BEAR_TRENDING = "bear_trending"
    SIDEWAYS_CHOPPY = "sideways_choppy"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"

@dataclass
class RegimeAnalysis:
    regime: MarketRegime
    confidence: float
    duration_days: int
    key_indicators: Dict[str, float]
    recommended_strategies: List[str]
    risk_level: str

class MarketRegimeAnalyzer:
    """Analyze current market regime and provide trading context"""
    
    def __init__(self):
        self.lookback_periods = {
            'short': 10,
            'medium': 20,
            'long': 50
        }
        
    async def analyze_current_regime(self, symbol: str = "SPY") -> RegimeAnalysis:
        """Analyze current market regime"""
        
        # Get historical data for analysis
        price_data = await self._get_price_data(symbol, days=60)
        volume_data = await self._get_volume_data(symbol, days=60)
        
        # Calculate key indicators
        indicators = self._calculate_regime_indicators(price_data, volume_data)
        
        # Determine regime
        regime = self._classify_regime(indicators)
        
        # Calculate confidence
        confidence = self._calculate_confidence(indicators, regime)
        
        # Get regime duration
        duration = await self._estimate_regime_duration(indicators)
        
        # Generate strategy recommendations
        recommendations = self._get_strategy_recommendations(regime, indicators)
        
        return RegimeAnalysis(
            regime=regime,
            confidence=confidence,
            duration_days=duration,
            key_indicators=indicators,
            recommended_strategies=recommendations,
            risk_level=self._assess_risk_level(regime, indicators)
        )
        
    def _calculate_regime_indicators(self, prices: List[float], volumes: List[float]) -> Dict[str, float]:
        """Calculate technical indicators for regime analysis"""
        
        # Convert to numpy arrays
        price_array = np.array(prices)
        volume_array = np.array(volumes)
        
        # Price-based indicators
        sma_20 = np.mean(price_array[-20:])
        sma_50 = np.mean(price_array[-50:])
        current_price = price_array[-1]
        
        # Trend strength
        trend_strength = (current_price - sma_50) / sma_50 * 100
        
        # Volatility (20-day rolling)
        returns = np.diff(price_array) / price_array[:-1]
        volatility = np.std(returns[-20:]) * np.sqrt(252) * 100
        
        # Volume analysis
        avg_volume = np.mean(volume_array[-20:])
        volume_trend = (volume_array[-1] - avg_volume) / avg_volume * 100
        
        # RSI calculation
        rsi = self._calculate_rsi(price_array)
        
        return {
            'trend_strength': trend_strength,
            'volatility': volatility,
            'rsi': rsi,
            'volume_trend': volume_trend,
            'price_vs_sma20': (current_price - sma_20) / sma_20 * 100,
            'sma_relationship': (sma_20 - sma_50) / sma_50 * 100
        }
        
    def _classify_regime(self, indicators: Dict[str, float]) -> MarketRegime:
        """Classify the current market regime"""
        
        trend_strength = indicators['trend_strength']
        volatility = indicators['volatility']
        rsi = indicators['rsi']
        
        # High volatility regime
        if volatility > 25:
            return MarketRegime.HIGH_VOLATILITY
            
        # Low volatility regime
        if volatility < 10:
            return MarketRegime.LOW_VOLATILITY
            
        # Trending regimes
        if abs(trend_strength) > 5:
            if trend_strength > 0 and rsi < 70:
                return MarketRegime.BULL_TRENDING
            elif trend_strength < 0 and rsi > 30:
                return MarketRegime.BEAR_TRENDING
                
        # Default to sideways/choppy
        return MarketRegime.SIDEWAYS_CHOPPY
        
    def _calculate_confidence(self, indicators: Dict[str, float], regime: MarketRegime) -> float:
        """Calculate confidence level for regime classification"""
        
        # Simplified confidence calculation
        trend_strength = abs(indicators['trend_strength'])
        volatility = indicators['volatility']
        
        base_confidence = 0.5
        
        # Higher confidence for stronger trends
        if trend_strength > 10:
            base_confidence += 0.3
        elif trend_strength > 5:
            base_confidence += 0.2
            
        # Adjust for volatility consistency
        if 10 <= volatility <= 20:  # Normal volatility range
            base_confidence += 0.1
            
        return min(base_confidence, 0.95)
        
    def _get_strategy_recommendations(self, regime: MarketRegime, indicators: Dict[str, float]) -> List[str]:
        """Get recommended trading strategies for current regime"""
        
        recommendations = []
        
        if regime == MarketRegime.BULL_TRENDING:
            recommendations = [
                "Momentum breakout strategies",
                "Trend following systems",
                "Buy-and-hold positions",
                "Call option strategies"
            ]
        elif regime == MarketRegime.BEAR_TRENDING:
            recommendations = [
                "Short selling strategies",
                "Put option strategies",
                "Inverse ETF positions",
                "Cash preservation"
            ]
        elif regime == MarketRegime.SIDEWAYS_CHOPPY:
            recommendations = [
                "Range trading strategies",
                "Mean reversion systems",
                "Iron condor options",
                "Short volatility strategies"
            ]
        elif regime == MarketRegime.HIGH_VOLATILITY:
            recommendations = [
                "Volatility trading strategies",
                "Straddle/strangle options",
                "Breakout strategies",
                "Reduced position sizing"
            ]
        else:  # LOW_VOLATILITY
            recommendations = [
                "Long volatility strategies",
                "Calendar spreads",
                "Covered call writing",
                "Momentum strategies"
            ]
            
        return recommendations
        
    def _assess_risk_level(self, regime: MarketRegime, indicators: Dict[str, float]) -> str:
        """Assess overall risk level"""
        
        volatility = indicators['volatility']
        
        if regime == MarketRegime.HIGH_VOLATILITY or volatility > 30:
            return "High"
        elif regime == MarketRegime.LOW_VOLATILITY and volatility < 10:
            return "Low"
        else:
            return "Medium"
            
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI indicator"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    async def _get_price_data(self, symbol: str, days: int) -> List[float]:
        """Get historical price data"""
        # This would connect to your market data service
        # Placeholder implementation
        return [100.0 + i * 0.5 for i in range(days)]
        
    async def _get_volume_data(self, symbol: str, days: int) -> List[float]:
        """Get historical volume data"""
        # This would connect to your market data service
        # Placeholder implementation
        return [1000000.0 + i * 10000 for i in range(days)]
        
    async def _estimate_regime_duration(self, indicators: Dict[str, float]) -> int:
        """Estimate how long current regime has been active"""
        # Simplified duration estimation
        return 15  # Default 15 days
