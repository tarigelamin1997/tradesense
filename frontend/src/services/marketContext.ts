
import { apiClient } from './api';

export interface MarketContext {
  symbol: string;
  date: string;
  market_condition: string;
  volatility: number;
  volume_profile: string;
  sector_performance: {
    sector: string;
    sector_performance: string;
    relative_strength: number;
  };
  economic_events: string[];
  technical_indicators: {
    rsi: number;
    macd_signal: string;
    moving_average_trend: string;
    support_level: number;
    resistance_level: number;
  };
  market_sentiment: {
    fear_greed_index: number;
    put_call_ratio: number;
    vix_level: number;
    sentiment_score: string;
  };
}

export interface MarketCondition {
  value: string;
  label: string;
  description: string;
}

export interface SectorPerformance {
  name: string;
  performance: string;
  change: string;
}

export interface EconomicEvent {
  date: string;
  event: string;
  impact: string;
  description: string;
}

export const marketContextService = {
  // Get market context for symbol and date
  async getMarketContext(symbol: string, tradeDate?: string): Promise<MarketContext> {
    const params = new URLSearchParams();
    if (tradeDate) {
      params.append('trade_date', tradeDate);
    }
    
    const response = await apiClient.get(`/trades/market-context/symbol/${symbol}?${params}`);
    return response.data.data;
  },

  // Tag trade with market context
  async tagTradeWithContext(tradeData: any): Promise<any> {
    const response = await apiClient.post('/trades/market-context/tag-trade', tradeData);
    return response.data.data;
  },

  // Get available market conditions
  async getMarketConditions(): Promise<MarketCondition[]> {
    const response = await apiClient.get('/trades/market-context/conditions');
    return response.data.data;
  },

  // Get sector performance
  async getSectorPerformance(): Promise<SectorPerformance[]> {
    const response = await apiClient.get('/trades/market-context/sectors');
    return response.data.data;
  },

  // Get economic events
  async getEconomicEvents(startDate?: string, endDate?: string): Promise<EconomicEvent[]> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await apiClient.get(`/trades/market-context/events?${params}`);
    return response.data.data;
  }
};
