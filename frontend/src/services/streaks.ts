
import { api } from './api';

export interface StreakAnalysis {
  max_win_streak: number;
  max_loss_streak: number;
  current_streak: number;
  current_streak_type: 'win' | 'loss' | 'neutral' | 'none';
  win_sessions: number;
  loss_sessions: number;
  neutral_sessions: number;
  total_sessions: number;
  consistency_score: number;
  session_breakdown: SessionBreakdown[];
  current_streak_details: StreakDetails;
  streak_patterns: StreakPatterns;
  performance_insights: string[];
}

export interface SessionBreakdown {
  date: string;
  pnl: number;
  trade_count: number;
  outcome: 'win' | 'loss' | 'neutral';
  avg_trade_pnl: number;
}

export interface StreakDetails {
  status: string;
  recommendation: string;
  latest_session_pnl?: number;
  latest_session_date?: string;
}

export interface StreakPatterns {
  avg_win_streak_length: number;
  avg_loss_streak_length: number;
  total_streaks: number;
  longest_overall_streak: number;
}

export interface StreakSummary {
  current_streak: number;
  current_streak_type: 'win' | 'loss' | 'neutral' | 'none';
  consistency_score: number;
  status_message: string;
  recommendation: string;
}

export const streaksService = {
  async getStreakAnalysis(): Promise<StreakAnalysis> {
    const response = await api.get('/analytics/streaks');
    return response.data.data;
  },

  async getStreakSummary(): Promise<StreakSummary> {
    const response = await api.get('/analytics/streaks/summary');
    return response.data.data;
  }
};
