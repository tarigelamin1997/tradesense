
import { api } from './api';

export interface StrategyMetrics {
  strategy_name: string;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_pnl_per_trade: number;
  avg_win: number;
  avg_loss: number;
  avg_risk_reward: number;
  profit_factor: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  edge_strength: number;
  consistency_score: number;
  trade_frequency: {
    trades_per_month: number;
    avg_days_between_trades: number;
  };
  largest_win: number;
  largest_loss: number;
  sharpe_ratio: number;
  kelly_criterion: number;
}

export interface EdgeStrengthAnalysis {
  strategies: Record<string, StrategyMetrics>;
  summary: {
    total_strategies: number;
    profitable_strategies: number;
    strong_edge_strategies: number;
    weak_edge_strategies: number;
    best_strategy: string | null;
    worst_strategy: string | null;
    total_trades_analyzed: number;
  };
  generated_at: string;
  filters_applied: {
    start_date?: string;
    end_date?: string;
    strategy_filter?: string;
    min_trades: number;
  };
}

export interface StrategyComparison {
  strategy: string;
  edge_strength: number;
  win_rate: number;
  profit_factor: number;
  total_pnl: number;
  sample_size: number;
  recommendation: string;
}

export interface StrategyComparisonResponse {
  comparison: StrategyComparison[];
  insights: string[];
  total_strategies_analyzed: number;
}

export interface StrategyRecommendation {
  strategy: string;
  type: 'data_collection' | 'scale_up' | 'review_or_stop';
  priority: 'low' | 'medium' | 'high';
  message: string;
  target: string;
}

export interface RecommendationsResponse {
  recommendations: StrategyRecommendation[];
  action_items: string[];
  summary: string;
}

export interface EdgeStrengthFilters {
  start_date?: string;
  end_date?: string;
  strategy_filter?: string;
  min_trades?: number;
}

class EdgeStrengthService {
  async getEdgeStrengthAnalysis(filters?: EdgeStrengthFilters): Promise<EdgeStrengthAnalysis> {
    const params = new URLSearchParams();
    
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.strategy_filter) params.append('strategy_filter', filters.strategy_filter);
    if (filters?.min_trades) params.append('min_trades', filters.min_trades.toString());
    
    const response = await api.get(`/analytics/edge-strength?${params.toString()}`);
    return response.data;
  }

  async getStrategyComparison(filters?: { start_date?: string; end_date?: string }): Promise<StrategyComparisonResponse> {
    const params = new URLSearchParams();
    
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    
    const response = await api.get(`/analytics/edge-strength/comparison?${params.toString()}`);
    return response.data;
  }

  async getStrategyDetails(strategyName: string, filters?: { start_date?: string; end_date?: string }) {
    const params = new URLSearchParams();
    
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    
    const response = await api.get(`/analytics/edge-strength/strategy/${encodeURIComponent(strategyName)}?${params.toString()}`);
    return response.data;
  }

  async getRecommendations(): Promise<RecommendationsResponse> {
    const response = await api.get('/analytics/edge-strength/recommendations');
    return response.data;
  }

  getEdgeStrengthColor(edgeStrength: number): string {
    if (edgeStrength >= 70) return 'text-green-600';
    if (edgeStrength >= 50) return 'text-yellow-600';
    if (edgeStrength >= 30) return 'text-orange-600';
    return 'text-red-600';
  }

  getEdgeStrengthBadgeColor(edgeStrength: number): string {
    if (edgeStrength >= 70) return 'bg-green-100 text-green-800';
    if (edgeStrength >= 50) return 'bg-yellow-100 text-yellow-800';
    if (edgeStrength >= 30) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  }

  getRecommendationColor(recommendation: string): string {
    if (recommendation === 'Scale up') return 'text-green-600';
    if (recommendation === 'Monitor closely') return 'text-yellow-600';
    if (recommendation === 'Needs improvement') return 'text-orange-600';
    if (recommendation === 'Consider stopping') return 'text-red-600';
    return 'text-gray-600';
  }

  getPriorityColor(priority: string): string {
    if (priority === 'high') return 'text-red-600';
    if (priority === 'medium') return 'text-yellow-600';
    return 'text-green-600';
  }
}

export const edgeStrengthService = new EdgeStrengthService();
