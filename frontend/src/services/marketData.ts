
import { api } from './api';

export interface MarketData {
  symbol: string;
  price: number;
  change_percent?: number;
  volume?: number;
  timestamp: string;
  market_open: boolean;
}

export interface MarketSentiment {
  symbol: string;
  sentiment_score: number;
  fear_greed_index: number;
  volatility_index: number;
  news_sentiment: number;
  timestamp: string;
}

export interface TradeContext {
  current_price?: number;
  price_change_percent?: number;
  sentiment_score: number;
  fear_greed_index: number;
  volatility_index: number;
  market_hours: boolean;
  session_type: string;
}

export interface TrendingSymbol {
  symbol: string;
  volume: number;
  change_percent: number;
}

class MarketDataService {
  async getCurrentPrice(symbol: string): Promise<MarketData | null> {
    try {
      const response = await api.get(`/market-data/current-price/${symbol}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching price for ${symbol}:`, error);
      return null;
    }
  }

  async getMarketSentiment(symbol: string): Promise<MarketSentiment | null> {
    try {
      const response = await api.get(`/market-data/sentiment/${symbol}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching sentiment for ${symbol}:`, error);
      return null;
    }
  }

  async getTradeContext(symbol: string, entryTime?: string): Promise<TradeContext | null> {
    try {
      const params = entryTime ? { entry_time: entryTime } : {};
      const response = await api.get(`/market-data/trade-context/${symbol}`, { params });
      return response.data;
    } catch (error) {
      console.error(`Error fetching trade context for ${symbol}:`, error);
      return null;
    }
  }

  async subscribeToSymbol(symbol: string): Promise<boolean> {
    try {
      await api.post(`/market-data/subscribe/${symbol}`);
      return true;
    } catch (error) {
      console.error(`Error subscribing to ${symbol}:`, error);
      return false;
    }
  }

  async unsubscribeFromSymbol(symbol: string): Promise<boolean> {
    try {
      await api.delete(`/market-data/unsubscribe/${symbol}`);
      return true;
    } catch (error) {
      console.error(`Error unsubscribing from ${symbol}:`, error);
      return false;
    }
  }

  async getMarketStatus(): Promise<any> {
    try {
      const response = await api.get('/market-data/market-status');
      return response.data;
    } catch (error) {
      console.error('Error fetching market status:', error);
      return null;
    }
  }

  async getTrendingSymbols(limit: number = 10): Promise<TrendingSymbol[]> {
    try {
      const response = await api.get('/market-data/symbols/trending', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching trending symbols:', error);
      return [];
    }
  }

  // Real-time WebSocket connection helper
  createWebSocketConnection(userId: string, onMessage: (data: any) => void): WebSocket {
    const ws = new WebSocket(`ws://localhost:5000/api/v1/market-data/ws/${userId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return ws;
  }
}

export const marketDataService = new MarketDataService();
