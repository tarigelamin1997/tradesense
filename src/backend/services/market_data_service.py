import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from core.db.session import engine
from models.trade import Trade

class MarketDataService:
    """Service for fetching and integrating real-time market data"""
    
    def __init__(self):
        self.base_url = "https://api.polygon.io/v2"
        self.api_key = "demo"  # Replace with actual API key
        
    async def get_market_conditions(self, symbol: str, timestamp: datetime) -> Dict[str, str]:
        """Get market conditions for a given symbol and timestamp"""
        try:
            async with httpx.AsyncClient() as client:
                # Get market data around the trade time
                date_str = timestamp.strftime("%Y-%m-%d")
                
                # Fetch daily market data
                response = await client.get(
                    f"{self.base_url}/aggs/ticker/{symbol}/range/1/day/{date_str}/{date_str}",
                    params={"apikey": self.api_key}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._analyze_market_conditions(data, timestamp)
                else:
                    return self._get_default_conditions()
                    
        except Exception as e:
            print(f"Market data fetch error: {e}")
            return self._get_default_conditions()
    
    def _analyze_market_conditions(self, data: Dict, timestamp: datetime) -> Dict[str, str]:
        """Analyze market data to determine conditions"""
        conditions = {}
        
        if "results" in data and data["results"]:
            result = data["results"][0]
            open_price = result.get("o", 0)
            close_price = result.get("c", 0)
            high_price = result.get("h", 0)
            low_price = result.get("l", 0)
            volume = result.get("v", 0)
            
            # Determine volatility
            daily_range = ((high_price - low_price) / open_price) * 100 if open_price > 0 else 0
            if daily_range > 3.0:
                conditions["volatility"] = "high"
            elif daily_range > 1.5:
                conditions["volatility"] = "medium"
            else:
                conditions["volatility"] = "low"
            
            # Determine trend
            price_change = ((close_price - open_price) / open_price) * 100 if open_price > 0 else 0
            if price_change > 2.0:
                conditions["trend"] = "strong_bullish"
            elif price_change > 0.5:
                conditions["trend"] = "bullish"
            elif price_change < -2.0:
                conditions["trend"] = "strong_bearish"
            elif price_change < -0.5:
                conditions["trend"] = "bearish"
            else:
                conditions["trend"] = "sideways"
            
            # Determine volume condition
            avg_volume = 1000000  # Default average volume
            if volume > avg_volume * 1.5:
                conditions["volume"] = "high"
            elif volume < avg_volume * 0.5:
                conditions["volume"] = "low"
            else:
                conditions["volume"] = "normal"
            
            # Market session
            hour = timestamp.hour
            if 9 <= hour < 11:
                conditions["session"] = "market_open"
            elif 11 <= hour < 15:
                conditions["session"] = "mid_day"
            elif 15 <= hour < 16:
                conditions["session"] = "market_close"
            else:
                conditions["session"] = "after_hours"
                
        return conditions
    
    def _get_default_conditions(self) -> Dict[str, str]:
        """Return default market conditions when data is unavailable"""
        return {
            "volatility": "medium",
            "trend": "sideways",
            "volume": "normal",
            "session": "mid_day"
        }
    
    async def enrich_trades_with_market_context(self, user_id: int) -> int:
        """Enrich user trades with market context data"""
        enriched_count = 0
        
        with Session(engine) as db:
            # Get trades without market context
            trades = db.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.market_context.is_(None)
            ).all()
            
            for trade in trades:
                try:
                    market_conditions = await self.get_market_conditions(
                        trade.symbol, 
                        trade.entry_time
                    )
                    
                    # Store market context as JSON
                    trade.market_context = market_conditions
                    enriched_count += 1
                    
                    # Commit in batches
                    if enriched_count % 10 == 0:
                        db.commit()
                        
                except Exception as e:
                    print(f"Error enriching trade {trade.id}: {e}")
                    continue
            
            db.commit()
            
        return enriched_count

# Global instance
market_data_service = MarketDataService()
