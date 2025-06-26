
import { api } from './api';

export interface AnalyticsSummary {
  total_trades: number;
  total_pnl: number;
  overall_win_rate: number;
  strategy_stats: Array<{
    name: string;
    total_trades: number;
    win_rate: number;
    total_pnl: number;
    avg_return: number;
    profit_factor: number;
    best_trade: number;
    worst_trade: number;
  }>;
  emotion_impact: Array<{
    emotion: string;
    trade_count: number;
    win_rate: number;
    net_pnl: number;
    impact_score: number;
  }>;
  trigger_analysis: Array<{
    trigger: string;
    usage_count: number;
    win_rate: number;
    net_result: number;
  }>;
  confidence_analysis: Array<{
    confidence_level: number;
    trade_count: number;
    win_rate: number;
    avg_pnl: number;
  }>;
  emotional_leaks: Array<{
    category: string;
    name: string;
    cost: number;
    frequency: number;
    description: string;
    severity: string;
  }>;
  most_profitable_emotion: string;
  most_costly_emotion: string;
  hesitation_cost: number;
  fomo_impact: number;
  revenge_trading_cost: number;
  confidence_vs_performance_correlation: number;
}

interface AnalyticsFilters {
  start?: string;
  end?: string;
  strategy_filter?: string;
}

class AnalyticsService {
  async getSummary(filters: AnalyticsFilters = {}): Promise<AnalyticsSummary> {
    const params = new URLSearchParams();
    
    if (filters.start) params.append('start_date', filters.start);
    if (filters.end) params.append('end_date', filters.end);
    if (filters.strategy_filter) params.append('strategy_filter', filters.strategy_filter);
    
    const queryString = params.toString();
    const url = `/analytics/summary${queryString ? `?${queryString}` : ''}`;
    
    const response = await api.get(url);
    return response.data;
  }

  async getEmotionImpact(): Promise<any> {
    const response = await api.get('/analytics/emotion-impact');
    return response.data;
  }

  async getStrategyPerformance(): Promise<any> {
    const response = await api.get('/analytics/strategy-performance');
    return response.data;
  }

  async getConfidenceCorrelation(): Promise<any> {
    const response = await api.get('/analytics/confidence-correlation');
    return response.data;
  }
}

export const analyticsService = new AnalyticsService();
