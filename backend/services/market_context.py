import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

class MarketContextEngine:
    """Enhanced market context analysis with full tagging system."""

    def __init__(self):
        self.market_indicators = {
            'SPY': 'S&P 500',
            'QQQ': 'NASDAQ',
            'VIX': 'Volatility Index',
            'DXY': 'Dollar Index'
        }

    async def get_market_context(self, trade_date: datetime) -> Dict:
        """Get comprehensive market context for a trade date."""
        try:
            context = {}

            # Get market data for trade date
            for symbol, name in self.market_indicators.items():
                data = await self._get_symbol_data(symbol, trade_date)
                context[symbol] = data

            # Generate market tags
            tags = self._generate_market_tags(context, trade_date)

            return {
                'trade_date': trade_date.isoformat(),
                'market_data': context,
                'tags': tags,
                'market_regime': self._determine_market_regime(context),
                'volatility_environment': self._assess_volatility(context.get('VIX', {}))
            }

        except Exception as e:
            logger.error(f"Market context error: {e}")
            return self._default_context(trade_date)

    async def _get_symbol_data(self, symbol: str, trade_date: datetime) -> Dict:
        """Get price data for symbol around trade date."""
        try:
            ticker = yf.Ticker(symbol)

            # Get 5 days of data around trade date
            start_date = trade_date - timedelta(days=5)
            end_date = trade_date + timedelta(days=1)

            hist = ticker.history(start=start_date, end=end_date)

            if hist.empty:
                return {}

            # Get closest trading day data
            closest_data = hist.iloc[-1] if not hist.empty else None

            if closest_data is None:
                return {}

            return {
                'price': float(closest_data['Close']),
                'volume': int(closest_data['Volume']),
                'high': float(closest_data['High']),
                'low': float(closest_data['Low']),
                'change_pct': self._calculate_change_pct(hist)
            }

        except Exception as e:
            logger.error(f"Error getting data for {symbol}: {e}")
            return {}

    def _calculate_change_pct(self, hist) -> float:
        """Calculate percentage change from previous day."""
        if len(hist) < 2:
            return 0.0

        current = hist.iloc[-1]['Close']
        previous = hist.iloc[-2]['Close']

        return ((current - previous) / previous) * 100

    def _generate_market_tags(self, context: Dict, trade_date: datetime) -> List[str]:
        """Generate comprehensive market context tags."""
        tags = []

        # Market direction tags
        spy_data = context.get('SPY', {})
        if spy_data.get('change_pct'):
            change = spy_data['change_pct']
            if change > 1:
                tags.append('strong_bullish_market')
            elif change > 0.5:
                tags.append('bullish_market')
            elif change < -1:
                tags.append('strong_bearish_market')
            elif change < -0.5:
                tags.append('bearish_market')
            else:
                tags.append('sideways_market')

        # Volatility tags
        vix_data = context.get('VIX', {})
        if vix_data.get('price'):
            vix_level = vix_data['price']
            if vix_level > 30:
                tags.append('high_volatility')
            elif vix_level > 20:
                tags.append('medium_volatility')
            else:
                tags.append('low_volatility')

        # Tech vs broader market
        spy_change = spy_data.get('change_pct', 0)
        qqq_change = context.get('QQQ', {}).get('change_pct', 0)

        if qqq_change > spy_change + 0.5:
            tags.append('tech_outperforming')
        elif spy_change > qqq_change + 0.5:
            tags.append('value_outperforming')

        # Day of week patterns
        weekday = trade_date.weekday()
        if weekday == 0:
            tags.append('monday_session')
        elif weekday == 4:
            tags.append('friday_session')
        elif weekday in [1, 2, 3]:
            tags.append('midweek_session')

        # Time-based tags
        hour = trade_date.hour
        if 9 <= hour <= 10:
            tags.append('market_open')
        elif 15 <= hour <= 16:
            tags.append('market_close')
        elif 11 <= hour <= 14:
            tags.append('midday_session')

        return tags

    def _determine_market_regime(self, context: Dict) -> str:
        """Determine overall market regime."""
        spy_data = context.get('SPY', {})
        vix_data = context.get('VIX', {})

        spy_change = spy_data.get('change_pct', 0)
        vix_level = vix_data.get('price', 20)

        if vix_level > 25 and spy_change < -0.5:
            return 'risk_off'
        elif vix_level < 15 and spy_change > 0.5:
            return 'risk_on'
        elif abs(spy_change) < 0.3:
            return 'consolidation'
        else:
            return 'trending'

    def _assess_volatility(self, vix_data: Dict) -> str:
        """Assess volatility environment."""
        vix_level = vix_data.get('price', 20)

        if vix_level > 35:
            return 'extreme_high'
        elif vix_level > 25:
            return 'high'
        elif vix_level > 15:
            return 'normal'
        else:
            return 'low'

    def _default_context(self, trade_date: datetime) -> Dict:
        """Return default context when data unavailable."""
        return {
            'trade_date': trade_date.isoformat(),
            'market_data': {},
            'tags': ['market_data_unavailable'],
            'market_regime': 'unknown',
            'volatility_environment': 'unknown'
        }

# Global instance
market_context_engine = MarketContextEngine()