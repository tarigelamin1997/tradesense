
import { apiClient } from './api';

export interface TimeSlot {
  weekday: string;
  hour: number;
  avg_pnl: number;
  total_pnl: number;
  trade_count: number;
  win_rate: number;
}

export interface SymbolStats {
  symbol: string;
  total_trades: number;
  total_pnl: number;
  avg_pnl: number;
  win_rate: number;
  profit_factor: number;
  best_trade: number;
  worst_trade: number;
  total_volume: number;
  avg_volume: number;
  trading_days: number;
  avg_trades_per_day: number;
  direction_bias: string;
  long_trades: number;
  short_trades: number;
  consistency_score: number;
}

export interface HeatmapInsight {
  type: string;
  message: string;
  data: any;
}

export interface HeatmapRecommendation {
  type: string;
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  expected_impact: string;
}

export interface TimeHeatmapData {
  total_pnl_matrix: Record<string, number[]>;
  avg_pnl_matrix: Record<string, number[]>;
  trade_count_matrix: Record<string, number[]>;
  win_rate_matrix: Record<string, number[]>;
  best_time_slots: TimeSlot[];
  worst_time_slots: TimeSlot[];
  total_trading_hours: number;
}

export interface SymbolStatsData {
  symbols: SymbolStats[];
  summary: {
    total_symbols: number;
    profitable_symbols: number;
    unprofitable_symbols: number;
    best_symbol: string | null;
    worst_symbol: string | null;
    most_traded_symbol: string | null;
    avg_symbols_per_day: number;
  };
}

export interface HeatmapData {
  time_heatmap: TimeHeatmapData;
  symbol_stats: SymbolStatsData;
  insights: {
    time_insights: HeatmapInsight[];
    symbol_insights: HeatmapInsight[];
    recommendations: HeatmapRecommendation[];
  };
  metadata: {
    total_trades: number;
    date_range: {
      start: string | null;
      end: string | null;
    };
    symbols_analyzed: number;
  };
}

export interface HeatmapResponse {
  success: boolean;
  data: HeatmapData;
}

export const heatmapService = {
  async getPerformanceHeatmap(
    startDate?: string,
    endDate?: string
  ): Promise<HeatmapData> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await apiClient.get<HeatmapResponse>(
      `/analytics/heatmap?${params.toString()}`
    );
    
    if (!response.data.success) {
      throw new Error('Failed to fetch heatmap data');
    }
    
    return response.data.data;
  },

  async getTimeHeatmapOnly(
    startDate?: string,
    endDate?: string
  ): Promise<{
    time_heatmap: TimeHeatmapData;
    insights: HeatmapInsight[];
    metadata: HeatmapData['metadata'];
  }> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await apiClient.get(
      `/analytics/heatmap/time?${params.toString()}`
    );
    
    if (!response.data.success) {
      throw new Error('Failed to fetch time heatmap data');
    }
    
    return response.data.data;
  },

  async getSymbolPerformanceOnly(
    startDate?: string,
    endDate?: string
  ): Promise<{
    symbol_stats: SymbolStatsData;
    insights: HeatmapInsight[];
    metadata: HeatmapData['metadata'];
  }> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await apiClient.get(
      `/analytics/heatmap/symbols?${params.toString()}`
    );
    
    if (!response.data.success) {
      throw new Error('Failed to fetch symbol performance data');
    }
    
    return response.data.data;
  }
};
