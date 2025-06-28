import { api } from './api';

export interface MarketQuote {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: string;
  source: string;
}

export interface MarketSentiment {
  symbol: string;
  sentiment_score: number;
  sentiment_label: string;
  news_count: number;
  volatility: number;
  rsi: number;
  ma_signal: string;
  timestamp: string;
}

export interface MarketContext {
  symbol: string;
  timestamp: string;
  context: {
    market_price?: number;
    market_change?: number;
    market_volume?: number;
    sentiment_score?: number;
    volatility?: number;
    rsi?: number;
    ma_signal?: string;
  };
}

export const marketDataService = {
  async getQuote(symbol: string, apiKey?: string): Promise<MarketQuote> {
    const params = new URLSearchParams();
    if (apiKey) params.append('api_key', apiKey);

    const response = await api.get(`/market-data/quote/${symbol}?${params}`);
    return response.data;
  },

  async getBatchQuotes(symbols: string, apiKey?: string): Promise<{ quotes: MarketQuote[] }> {
    const params = new URLSearchParams({ symbols });
    if (apiKey) params.append('api_key', apiKey);

    const response = await api.get(`/market-data/quotes/batch?${params}`);
    return response.data;
  },

  async getMarketSentiment(symbol: string): Promise<MarketSentiment> {
    const response = await api.get(`/market-data/sentiment/${symbol}`);
    return response.data;
  },

  async getWatchlist(): Promise<{ watchlist: MarketQuote[] }> {
    const response = await api.get('/market-data/watchlist');
    return response.data;
  },

  async addToWatchlist(symbol: string): Promise<{ message: string }> {
    const response = await api.post(`/market-data/watchlist/${symbol}`);
    return response.data;
  },

  async removeFromWatchlist(symbol: string): Promise<{ message: string }> {
    const response = await api.delete(`/market-data/watchlist/${symbol}`);
    return response.data;
  },

  async getMarketContext(symbol: string, timestamp?: string): Promise<MarketContext> {
    const params = new URLSearchParams();
    if (timestamp) params.append('timestamp', timestamp);

    const response = await api.get(`/market-data/context/${symbol}?${params}`);
    return response.data;
  },

  async getHealthStatus(): Promise<{ status: string; message: string; timestamp: string }> {
    const response = await api.get('/market-data/health');
    return response.data;
  }
};