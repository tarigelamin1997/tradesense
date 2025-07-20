import { api } from './client-safe';
import type { Trade } from './trades';

// AI Analysis Types
export interface TradeScore {
  overall_score: number; // 0-100
  execution_score: number;
  timing_score: number;
  strategy_score: number;
  risk_reward_ratio: number;
  pnl: number;
  pnl_percentage: number;
  insights: string[];
  recommendations: string[];
  market_context: MarketContext;
}

export interface TradeCritique {
  summary: string;
  suggestion: string;
  confidence: number; // 1-10
  tags: string[];
  technical_analysis: string;
  psychological_analysis: string;
  risk_assessment: string;
}

export interface BehavioralInsights {
  emotional_state: string;
  consistency_rating: number;
  discipline_score: number;
  risk_profile: string;
  patterns_detected: PatternDetection[];
  improvement_areas: string[];
  streaks: StreakAnalysis;
}

export interface PatternDetection {
  pattern_type: string;
  frequency: number;
  impact_on_pnl: number;
  description: string;
  examples: string[];
  recommendations: string;
}

export interface StreakAnalysis {
  current_streak: number;
  streak_type: 'winning' | 'losing' | 'neutral';
  best_streak: number;
  worst_streak: number;
  average_streak_length: number;
}

export interface EdgeStrength {
  strategy: string;
  win_rate: number;
  profit_factor: number;
  sharpe_ratio: number;
  kelly_criterion: number;
  sample_size: number;
  confidence_level: number;
  market_conditions: string[];
}

export interface MarketContext {
  regime: 'bull' | 'bear' | 'sideways';
  volatility: 'low' | 'medium' | 'high';
  trend_strength: number;
  support_levels: number[];
  resistance_levels: number[];
  recommendation: string;
}

export interface EmotionalAnalytics {
  dominant_emotions: Array<{
    emotion: string;
    frequency: number;
    impact: number;
  }>;
  emotional_consistency: number;
  best_performing_emotion: string;
  worst_performing_emotion: string;
  recommendations: string[];
}

export interface PreTradeAnalysis {
  should_take_trade: boolean;
  confidence_score: number;
  risk_score: number;
  pattern_matches: Array<{
    pattern: string;
    similarity: number;
    historical_outcome: string;
  }>;
  market_alignment: boolean;
  psychological_readiness: number;
  suggested_position_size: number;
  warnings: string[];
}

export interface AIInsightsSummary {
  trade_score: TradeScore;
  critique: TradeCritique;
  behavioral_insights: BehavioralInsights;
  edge_strength: EdgeStrength[];
  market_context: MarketContext;
  emotional_analytics: EmotionalAnalytics;
}

// AI API Service
export const aiApi = {
  // Trade Intelligence
  async getTradeScore(tradeId: string): Promise<TradeScore> {
    return api.get(`/api/v1/ai/trades/${tradeId}/score`);
  },

  async getTradeScoreBulk(tradeIds: string[]): Promise<Record<string, TradeScore>> {
    return api.post('/api/v1/ai/trades/score/bulk', { trade_ids: tradeIds });
  },

  // Trade Critique
  async getTradeCritique(tradeId: string): Promise<TradeCritique> {
    return api.get(`/api/v1/critique/trades/${tradeId}`);
  },

  async regenerateCritique(tradeId: string): Promise<TradeCritique> {
    return api.post(`/api/v1/critique/trades/${tradeId}/regenerate`);
  },

  // Behavioral Analytics
  async getBehavioralInsights(timeframe: 'week' | 'month' | 'quarter' | 'year' = 'month'): Promise<BehavioralInsights> {
    return api.get(`/api/v1/ai/behavioral/insights?timeframe=${timeframe}`);
  },

  async getPatternDetection(): Promise<PatternDetection[]> {
    return api.get('/api/v1/ai/patterns/detect');
  },

  // Edge Strength Analysis
  async getEdgeStrength(): Promise<EdgeStrength[]> {
    return api.get('/api/v1/ai/edge/strength');
  },

  async getEdgeByStrategy(strategy: string): Promise<EdgeStrength> {
    return api.get(`/api/v1/ai/edge/strategy/${strategy}`);
  },

  // Market Context
  async getMarketContext(symbol?: string): Promise<MarketContext> {
    return api.get('/api/v1/ai/market/context', { params: { symbol } });
  },

  async getMarketRegime(): Promise<{ regime: string; confidence: number; factors: string[] }> {
    return api.get('/api/v1/ai/market/regime');
  },

  // Emotional Analytics
  async getEmotionalAnalytics(timeframe: 'week' | 'month' | 'quarter' = 'month'): Promise<EmotionalAnalytics> {
    return api.get(`/api/v1/ai/emotional/analytics?timeframe=${timeframe}`);
  },

  async getEmotionalImpact(): Promise<any> {
    return api.get('/api/v1/ai/emotional/impact');
  },

  // Pre-Trade Analysis
  async analyzePreTrade(trade: Partial<Trade>): Promise<PreTradeAnalysis> {
    return api.post('/api/v1/ai/pre-trade/analyze', trade);
  },

  // AI Insights Summary
  async getAIInsightsSummary(): Promise<AIInsightsSummary> {
    return api.get('/api/v1/ai/insights/summary');
  },

  // Pattern Recognition
  async detectPatterns(timeframe: 'week' | 'month' | 'all' = 'month'): Promise<PatternDetection[]> {
    return api.get(`/api/v1/ai/patterns?timeframe=${timeframe}`);
  },

  async getPatternHistory(patternType: string): Promise<any> {
    return api.get(`/api/v1/ai/patterns/${patternType}/history`);
  },

  // AI Recommendations
  async getRecommendations(): Promise<{
    immediate: string[];
    weekly: string[];
    improvement_plan: string[];
  }> {
    return api.get('/api/v1/ai/recommendations');
  },

  // Risk Analysis
  async getRiskAnalysis(): Promise<{
    current_risk_score: number;
    var_95: number;
    var_99: number;
    max_drawdown_predicted: number;
    position_sizing_recommendation: number;
    warnings: string[];
  }> {
    return api.get('/api/v1/ai/risk/analysis');
  },

  // Real-time scoring via WebSocket
  subscribeToLiveScoring(onScore: (score: TradeScore) => void): () => void {
    // This would connect to WebSocket for real-time updates
    // Implementation depends on WebSocket setup
    return () => {
      // Cleanup function
    };
  }
};