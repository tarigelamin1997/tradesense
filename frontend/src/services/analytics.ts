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
    trade_count?: number; // Add this for strategy breakdown
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
  performance_over_time?: {
    dates: string[];
    cumulative_pnl: number[];
  };
  monthly_stats?: Array<{
    month: string;
    trade_count: number;
    total_pnl: number;
  }>;
}

interface AnalyticsFilters {
  start?: string;
  end?: string;
  strategy_filter?: string;
}

const getPlaybookMetrics = async (playbookName: string, timeRange: string = '6M') => {
  const response = await api.get(`/api/v1/analytics/playbooks/${encodeURIComponent(playbookName)}/metrics`, {
    params: { time_range: timeRange }
  });
  return response.data;
};

export const analyticsService = {
  getSummary: async (filters: AnalyticsFilters = {}) => {
    const params = new URLSearchParams();

    if (filters.start) params.append('start_date', filters.start);
    if (filters.end) params.append('end_date', filters.end);
    if (filters.strategy_filter) params.append('strategy_filter', filters.strategy_filter);

    const queryString = params.toString();
    const url = `/api/v1/analytics/summary${queryString ? `?${queryString}` : ''}`;

    try {
      console.log('Making request to:', url);
      console.log('With params:', queryString);
      console.log('Full URL would be:', `http://localhost:8000${url}`);
      
      const response = await api.get(url);
      console.log('Analytics API response:', response);
      
      // Backend returns wrapped response: { success: true, data: {...}, message: "..." }
      // We need to extract the actual data
      if (response.data && response.data.data) {
        console.log('Extracting data from wrapped response');
        return response.data.data;
      }
      
      return response.data;
    } catch (error: any) {
      console.error('Analytics API error details:', {
        message: error.message,
        response: error.response,
        request: error.request,
        config: error.config
      });
      throw error;
    }
  },

  getEmotionImpact: async () => {
    const response = await api.get('/api/v1/analytics/emotion-impact');
    return response.data?.data || response.data;
  },

  getStrategyPerformance: async () => {
    const response = await api.get('/api/v1/analytics/strategy-performance');
    return response.data?.data || response.data;
  },

  getConfidenceCorrelation: async () => {
    const response = await api.get('/api/v1/analytics/confidence-correlation');
    return response.data?.data || response.data;
  },
  getPlaybookMetrics,

  async getStreakAnalysis(timeframe: string = '3M'): Promise<any> {
    const response = await api.get(`/api/v1/analytics/streaks?timeframe=${timeframe}`);
    return response.data;
  },

  async getPlaybookComparison(timeframe: string = '3M'): Promise<any> {
    const response = await api.get(`/api/v1/analytics/playbooks/comparison?timeframe=${timeframe}`);
    return response.data;
  },

  async getAvailablePlaybooks(): Promise<any> {
    const response = await api.get(`/api/v1/analytics/playbooks/available`);
    return response.data;
  },
};