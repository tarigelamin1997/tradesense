
import asyncio
import websockets
import json
from typing import Dict, List, Optional, Callable
from datetime import datetime
import aiohttp
from sqlalchemy.orm import Session
from backend.core.db.session import get_db

class RealTimeMarketService:
    """Real-time market data service with multiple data sources"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.active_symbols: set = set()
        self.market_data_cache: Dict[str, Dict] = {}
        self.is_running = False
        
    async def start_market_feeds(self):
        """Start real-time market data feeds"""
        self.is_running = True
        
        # Start multiple data source tasks
        tasks = [
            self._polygon_websocket(),
            self._alpha_vantage_feed(),
            self._yahoo_finance_feed()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _polygon_websocket(self):
        """Polygon.io WebSocket feed"""
        try:
            uri = "wss://socket.polygon.io/stocks"
            async with websockets.connect(uri) as websocket:
                # Subscribe to authentication
                auth_msg = {
                    "action": "auth",
                    "params": "YOUR_POLYGON_API_KEY"  # Replace with actual key
                }
                await websocket.send(json.dumps(auth_msg))
                
                # Subscribe to symbols
                subscribe_msg = {
                    "action": "subscribe",
                    "params": "T.*"  # All trades
                }
                await websocket.send(json.dumps(subscribe_msg))
                
                while self.is_running:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        await self._process_market_data(data, "polygon")
                    except Exception as e:
                        print(f"Polygon WebSocket error: {e}")
                        
        except Exception as e:
            print(f"Failed to connect to Polygon: {e}")
    
    async def _alpha_vantage_feed(self):
        """Alpha Vantage API polling"""
        symbols = ["SPY", "QQQ", "AAPL", "TSLA", "MSFT"]
        
        while self.is_running:
            try:
                async with aiohttp.ClientSession() as session:
                    for symbol in symbols:
                        url = f"https://www.alphavantage.co/query"
                        params = {
                            "function": "GLOBAL_QUOTE",
                            "symbol": symbol,
                            "apikey": "YOUR_ALPHA_VANTAGE_KEY"  # Replace with actual key
                        }
                        
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                await self._process_market_data(data, "alphavantage")
                
                await asyncio.sleep(5)  # Poll every 5 seconds
                
            except Exception as e:
                print(f"Alpha Vantage error: {e}")
                await asyncio.sleep(10)
    
    async def _yahoo_finance_feed(self):
        """Yahoo Finance backup feed"""
        symbols = ["^GSPC", "^IXIC", "^DJI"]  # Major indices
        
        while self.is_running:
            try:
                async with aiohttp.ClientSession() as session:
                    for symbol in symbols:
                        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                        
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                await self._process_market_data(data, "yahoo")
                
                await asyncio.sleep(15)  # Poll every 15 seconds
                
            except Exception as e:
                print(f"Yahoo Finance error: {e}")
                await asyncio.sleep(30)
    
    async def _process_market_data(self, data: Dict, source: str):
        """Process and distribute market data"""
        try:
            processed_data = self._normalize_market_data(data, source)
            
            if processed_data:
                symbol = processed_data.get("symbol")
                if symbol:
                    # Update cache
                    self.market_data_cache[symbol] = processed_data
                    
                    # Notify subscribers
                    if symbol in self.subscribers:
                        for callback in self.subscribers[symbol]:
                            try:
                                await callback(processed_data)
                            except Exception as e:
                                print(f"Callback error: {e}")
                                
        except Exception as e:
            print(f"Market data processing error: {e}")
    
    def _normalize_market_data(self, data: Dict, source: str) -> Optional[Dict]:
        """Normalize data from different sources"""
        try:
            if source == "polygon":
                if data.get("ev") == "T":  # Trade event
                    return {
                        "symbol": data.get("sym"),
                        "price": data.get("p"),
                        "volume": data.get("s"),
                        "timestamp": data.get("t"),
                        "source": source
                    }
            
            elif source == "alphavantage":
                quote = data.get("Global Quote", {})
                if quote:
                    return {
                        "symbol": quote.get("01. symbol"),
                        "price": float(quote.get("05. price", 0)),
                        "change": float(quote.get("09. change", 0)),
                        "change_percent": quote.get("10. change percent"),
                        "timestamp": datetime.now().isoformat(),
                        "source": source
                    }
            
            elif source == "yahoo":
                result = data.get("chart", {}).get("result", [])
                if result:
                    meta = result[0].get("meta", {})
                    return {
                        "symbol": meta.get("symbol"),
                        "price": meta.get("regularMarketPrice"),
                        "change": meta.get("regularMarketPrice", 0) - meta.get("previousClose", 0),
                        "timestamp": datetime.now().isoformat(),
                        "source": source
                    }
                    
        except Exception as e:
            print(f"Data normalization error: {e}")
            
        return None
    
    def subscribe_to_symbol(self, symbol: str, callback: Callable):
        """Subscribe to real-time data for a symbol"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
        self.active_symbols.add(symbol)
    
    def unsubscribe_from_symbol(self, symbol: str, callback: Callable):
        """Unsubscribe from symbol updates"""
        if symbol in self.subscribers:
            if callback in self.subscribers[symbol]:
                self.subscribers[symbol].remove(callback)
            
            if not self.subscribers[symbol]:
                del self.subscribers[symbol]
                self.active_symbols.discard(symbol)
    
    def get_latest_price(self, symbol: str) -> Optional[Dict]:
        """Get latest cached price for symbol"""
        return self.market_data_cache.get(symbol)
    
    async def stop(self):
        """Stop all market data feeds"""
        self.is_running = False
        self.subscribers.clear()
        self.active_symbols.clear()
        self.market_data_cache.clear()

# Global market service instance
market_service = RealTimeMarketService()
