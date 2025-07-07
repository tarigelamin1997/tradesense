
import { api } from './api';

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  display_name: string;
  consistency_score: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  risk_adjusted_return: number;
  account_count: number;
  joined_date: string;
}

export interface GlobalLeaderboard {
  timeframe: string;
  metric: string;
  total_participants: number;
  last_updated: string;
  rankings: LeaderboardEntry[];
}

export interface UserRanking {
  user_id: string;
  global_ranking: {
    consistency_percentile: number;
    win_rate_percentile: number;
    profit_factor_percentile: number;
    risk_adjusted_return_percentile: number;
    overall_rank: number;
    total_users: number;
  };
  performance_summary: any;
  improvement_suggestions: string[];
  leaderboard_status: {
    opted_in: boolean;
    display_name: string;
    joined_leaderboard: string;
    privacy_level: string;
  };
  peer_comparison: any;
}

export interface CrossAccountAnalytics {
  aggregate_performance: any;
  account_comparison: any[];
  insights: string[];
  recommendations: string[];
}

export const leaderboardService = {
  async getGlobalLeaderboard(params?: {
    limit?: number;
    metric?: 'overall' | 'consistency' | 'win_rate' | 'profit_factor' | 'volume';
    timeframe?: 'all_time' | '30d' | '90d' | '1y';
  }): Promise<GlobalLeaderboard> {
    const response = await api.get('/leaderboard/global', { params });
    return response.data;
  },

  async getMyRanking(): Promise<UserRanking> {
    const response = await api.get('/leaderboard/my-ranking');
    return response.data;
  },

  async getCrossAccountAnalytics(): Promise<CrossAccountAnalytics> {
    const response = await api.get('/leaderboard/cross-account');
    return response.data;
  },

  async getAccountComparison(): Promise<any[]> {
    const response = await api.get('/leaderboard/account-comparison');
    return response.data;
  },

  async optIntoLeaderboard(): Promise<{ message: string; status: boolean }> {
    const response = await api.post('/leaderboard/opt-in');
    return response.data;
  },

  async optOutOfLeaderboard(): Promise<{ message: string; status: boolean }> {
    const response = await api.post('/leaderboard/opt-out');
    return response.data;
  }
};
