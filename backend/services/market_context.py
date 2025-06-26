
"""
Market Context Service for TradeSense
Integrates market data and provides context tags for trades
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
from enum import Enum

logger = logging.getLogger(__name__)

class MarketCondition(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    LOW_VOLUME = "low_volume"
    HIGH_VOLUME = "high_volume"

class MarketContextService:
    """Service for analyzing market conditions and tagging trades"""
    
    def __init__(self):
        self.cache = {}
        self.cache_expiry = timedelta(minutes=15)
        
    async def get_market_context(self, symbol: str, trade_date: datetime) -> Dict[str, Any]:
        """Get market context for a specific symbol and date"""
        cache_key = f"{symbol}_{trade_date.date()}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
            
        try:
            # Simulate market data fetch (replace with real API)
            context = await self._fetch_market_data(symbol, trade_date)
            
            # Cache the result
            self.cache[cache_key] = {
                'data': context,
                'timestamp': datetime.now()
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error fetching market context for {symbol}: {e}")
            return self._get_default_context()
    
    async def _fetch_market_data(self, symbol: str, trade_date: datetime) -> Dict[str, Any]:
        """Fetch market data from external API (simulated)"""
        # This would integrate with real market data APIs like:
        # - Alpha Vantage
        # - IEX Cloud  
        # - Yahoo Finance
        # - Polygon.io
        
        # Simulated market context based on symbol patterns
        context = {
            'symbol': symbol,
            'date': trade_date.isoformat(),
            'market_condition': self._analyze_market_condition(symbol),
            'volatility': self._calculate_volatility(symbol),
            'volume_profile': self._analyze_volume(symbol),
            'sector_performance': self._get_sector_context(symbol),
            'economic_events': self._get_economic_events(trade_date),
            'technical_indicators': self._get_technical_indicators(symbol),
            'market_sentiment': self._get_market_sentiment(symbol)
        }
        
        return context
    
    def _analyze_market_condition(self, symbol: str) -> str:
        """Analyze overall market condition"""
        # Simplified logic - would use real technical analysis
        if 'SPY' in symbol or 'QQQ' in symbol:
            return MarketCondition.BULLISH.value
        elif 'VIX' in symbol:
            return MarketCondition.VOLATILE.value
        else:
            return MarketCondition.SIDEWAYS.value
    
    def _calculate_volatility(self, symbol: str) -> float:
        """Calculate volatility score (0-100)"""
        # Simplified volatility calculation
        import random
        return round(random.uniform(10, 80), 2)
    
    def _analyze_volume(self, symbol: str) -> str:
        """Analyze volume profile"""
        import random
        volume_ratio = random.uniform(0.5, 2.0)
        
        if volume_ratio > 1.5:
            return MarketCondition.HIGH_VOLUME.value
        elif volume_ratio < 0.8:
            return MarketCondition.LOW_VOLUME.value
        else:
            return "normal_volume"
    
    def _get_sector_context(self, symbol: str) -> Dict[str, Any]:
        """Get sector-specific context"""
        # Map symbols to sectors (simplified)
        sector_map = {
            'AAPL': 'Technology',
            'MSFT': 'Technology', 
            'GOOGL': 'Technology',
            'TSLA': 'Automotive',
            'SPY': 'Market Index',
            'QQQ': 'Technology Index'
        }
        
        sector = sector_map.get(symbol, 'Unknown')
        
        return {
            'sector': sector,
            'sector_performance': 'outperforming' if sector == 'Technology' else 'neutral',
            'relative_strength': round(random.uniform(0.8, 1.2), 2)
        }
    
    def _get_economic_events(self, trade_date: datetime) -> List[str]:
        """Get economic events for the trade date"""
        # Simplified economic events
        events = []
        
        if trade_date.weekday() == 4:  # Friday
            events.append('Non-Farm Payrolls')
        elif trade_date.day <= 7:  # First week of month
            events.append('CPI Release')
        elif trade_date.day % 10 == 0:  # Every 10th day
            events.append('Fed Meeting')
            
        return events
    
    def _get_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """Get technical indicators"""
        import random
        
        return {
            'rsi': round(random.uniform(20, 80), 2),
            'macd_signal': random.choice(['bullish', 'bearish', 'neutral']),
            'moving_average_trend': random.choice(['uptrend', 'downtrend', 'sideways']),
            'support_level': round(random.uniform(100, 200), 2),
            'resistance_level': round(random.uniform(200, 300), 2)
        }
    
    def _get_market_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get market sentiment indicators"""
        import random
        
        return {
            'fear_greed_index': random.randint(0, 100),
            'put_call_ratio': round(random.uniform(0.5, 1.5), 2),
            'vix_level': round(random.uniform(10, 40), 2),
            'sentiment_score': random.choice(['bullish', 'bearish', 'neutral'])
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
            
        cache_time = self.cache[cache_key]['timestamp']
        return datetime.now() - cache_time < self.cache_expiry
    
    def _get_default_context(self) -> Dict[str, Any]:
        """Get default context when API fails"""
        return {
            'symbol': 'UNKNOWN',
            'date': datetime.now().isoformat(),
            'market_condition': 'unknown',
            'volatility': 0.0,
            'volume_profile': 'unknown',
            'sector_performance': {'sector': 'Unknown'},
            'economic_events': [],
            'technical_indicators': {},
            'market_sentiment': {}
        }

    async def tag_trade_with_context(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add market context tags to a trade"""
        symbol = trade_data.get('symbol', '')
        trade_date = datetime.fromisoformat(trade_data.get('entry_time', ''))
        
        context = await self.get_market_context(symbol, trade_date)
        
        # Generate context tags
        tags = []
        
        # Market condition tags
        tags.append(f"market_{context['market_condition']}")
        
        # Volatility tags
        if context['volatility'] > 60:
            tags.append("high_volatility")
        elif context['volatility'] < 20:
            tags.append("low_volatility")
            
        # Volume tags
        tags.append(f"volume_{context['volume_profile']}")
        
        # Sector tags
        sector_info = context['sector_performance']
        if sector_info['sector'] != 'Unknown':
            tags.append(f"sector_{sector_info['sector'].lower()}")
            
        # Economic event tags
        for event in context['economic_events']:
            tags.append(f"event_{event.lower().replace(' ', '_')}")
            
        # Technical indicator tags
        tech_indicators = context['technical_indicators']
        if 'macd_signal' in tech_indicators:
            tags.append(f"macd_{tech_indicators['macd_signal']}")
            
        # Add tags to trade data
        trade_data['market_context_tags'] = tags
        trade_data['market_context'] = context
        
        return trade_data

# Global instance
market_context_service = MarketContextService()
