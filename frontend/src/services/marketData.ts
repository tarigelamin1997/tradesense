import { apiClient } from './api';

export interface MarketQuote {
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: string;
  market_regime: string;
  volatility: number;
  support_resistance: {
    support: number;
    resistance: number;
  };
}

export interface MarketSentiment {
  sentiment_score: number;
  sentiment_label: 'bullish' | 'bearish' | 'neutral';
  confidence: number;
  news_count: number;
  social_media_mentions: number;
  analyst_ratings: {
    buy: number;
    hold: number;
    sell: number;
  };
  fear_greed_index: number;
  institutional_flow: 'inflow' | 'outflow';
}

export interface EconomicEvent {
  name: string;
  date: string;
  time: string;
  impact: 'high' | 'medium' | 'low';
  currency: string;
  forecast: string;
  previous: string;
}

export interface MarketContext {
  live_quote: MarketQuote;
  sentiment: MarketSentiment;
  regime: string;
  economic_events: EconomicEvent[];
  market_hours: {
    current_session: string;
    is_active: boolean;
    next_open?: string;
  };
  context_score: number;
}

export const marketDataService = {
  async getQuote(symbol: string): Promise<MarketQuote> {
    const response = await apiClient.get(`/market-data/quotes/${symbol}`);
    return response.data;
  },

  async getBatchQuotes(symbols: string[]): Promise<Record<string, MarketQuote>> {
    const response = await apiClient.get('/market-data/quotes/batch', {
      params: { symbols }
    });
    return response.data;
  },

  async getSentiment(symbol: string): Promise<MarketSentiment> {
    const response = await apiClient.get(`/market-data/sentiment/${symbol}`);
    return response.data;
  },

  async getMarketRegime(symbol: string): Promise<{ symbol: string; regime: string }> {
    const response = await apiClient.get(`/market-data/regime/${symbol}`);
    return response.data;
  },

  async getEconomicCalendar(daysAhead: number = 7): Promise<EconomicEvent[]> {
    const response = await apiClient.get('/market-data/economic-calendar', {
      params: { days_ahead: daysAhead }
    });
    return response.data;
  },

  async getMarketContext(symbol: string): Promise<MarketContext> {
    const response = await apiClient.get(`/market-data/context/${symbol}`);
    return response.data;
  },

  async getMarketHours(): Promise<{
    current_session: string;
    is_active: boolean;
    next_open?: string;
  }> {
    const response = await apiClient.get('/market-data/market-hours');
    return response.data;
  }
};