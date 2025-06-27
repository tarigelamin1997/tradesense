
import { api } from './api';

export interface MarketDataSubscription {
  symbol: string;
  provider: string;
  subscribed_at: string;
  last_update: string | null;
}

export interface MarketData {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  market_cap: number;
  pe_ratio: number;
  fifty_two_week_high: number;
  fifty_two_week_low: number;
  market_state: string;
}

export interface MarketContext {
  symbol: string;
  trade_time: string;
  market_price_at_analysis: number;
  market_state: string;
  volume: number;
  volatility_indicator: string;
  market_trend: string;
  support_resistance: {
    support: number;
    resistance: number;
    current_price: number;
    distance_to_support: number;
    distance_to_resistance: number;
  };
}

export interface TimingAnalysis {
  symbol: string;
  entry_time: string;
  market_context: MarketContext;
  timing_analysis: {
    market_volatility: string;
    market_trend: string;
    timing_score: number;
    recommendations: string[];
  };
}

export const marketDataService = {
  async subscribeToSymbol(symbol: string, provider: string = 'yahoo_finance') {
    const response = await api.get(`/market-data/subscribe/${symbol}?provider=${provider}`);
    return response.data;
  },

  async unsubscribeFromSymbol(symbol: string) {
    const response = await api.get(`/market-data/unsubscribe/${symbol}`);
    return response.data;
  },

  async getMarketData(symbol: string) {
    const response = await api.get(`/market-data/data/${symbol}`);
    return response.data;
  },

  async getActiveSubscriptions(): Promise<{ success: boolean; subscriptions: Record<string, MarketDataSubscription>; count: number }> {
    const response = await api.get('/market-data/subscriptions');
    return response.data;
  },

  async getMarketContext(symbol: string, tradeTime?: string): Promise<{ success: boolean; context: MarketContext }> {
    const params = tradeTime ? `?trade_time=${tradeTime}` : '';
    const response = await api.get(`/market-data/context/${symbol}${params}`);
    return response.data;
  },

  async analyzeTradeTimingn(tradeData: { symbol: string; entry_time: string }): Promise<{ success: boolean; analysis: TimingAnalysis }> {
    const response = await api.post('/market-data/analyze-trade-timing', tradeData);
    return response.data;
  },

  // Utility functions
  formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  },

  formatVolume(volume: number): string {
    if (volume >= 1000000) {
      return `${(volume / 1000000).toFixed(1)}M`;
    } else if (volume >= 1000) {
      return `${(volume / 1000).toFixed(1)}K`;
    }
    return volume.toString();
  },

  getChangeColor(change: number): string {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  }
};
