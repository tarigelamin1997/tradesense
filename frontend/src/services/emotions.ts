
import api from './api';

export interface EmotionalReflection {
  trade_id: string;
  emotional_tags: string[];
  reflection_notes: string;
  emotional_score: number;
  executed_plan: boolean;
  post_trade_mood: string;
}

export interface EmotionPerformanceStats {
  [emotion: string]: {
    count: number;
    avg_pnl: number;
    win_rate: number;
    avg_emotional_score: number;
    plan_adherence_rate: number;
  };
}

export interface PlanExecutionAnalysis {
  followed_plan: {
    count: number;
    avg_pnl: number;
    win_rate: number;
  };
  broke_plan: {
    count: number;
    avg_pnl: number;
    win_rate: number;
  };
  plan_adherence_impact: {
    pnl_difference: number;
    win_rate_difference: number;
  };
}

export interface EmotionalTrends {
  weekly_trends: Array<{
    week: string;
    avg_emotional_score: number;
    plan_adherence_rate: number;
    avg_pnl: number;
    trade_count: number;
  }>;
  overall_improvement: {
    trend: 'improving' | 'declining' | 'stable' | 'insufficient_data';
    slope: number;
  };
}

class EmotionsService {
  async getEmotionalStates() {
    const response = await api.get('/emotions/states');
    return response.data;
  }

  async updateTradeReflection(reflection: EmotionalReflection) {
    const response = await api.post(
      `/emotions/trades/${reflection.trade_id}/reflection`,
      reflection
    );
    return response.data;
  }

  async getPerformanceCorrelation(): Promise<EmotionPerformanceStats> {
    const response = await api.get('/emotions/analytics/performance-correlation');
    return response.data;
  }

  async getPlanExecutionAnalysis(): Promise<PlanExecutionAnalysis> {
    const response = await api.get('/emotions/analytics/plan-execution');
    return response.data;
  }

  async getEmotionalTrends(days: number = 30): Promise<EmotionalTrends> {
    const response = await api.get(`/emotions/analytics/trends?days=${days}`);
    return response.data;
  }

  async getEmotionalInsights(): Promise<string[]> {
    const response = await api.get('/emotions/insights');
    return response.data.insights;
  }
}

export default new EmotionsService();
