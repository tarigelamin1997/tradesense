
import { apiRequest } from './api';

export interface PatternCluster {
  id: string;
  user_id: string;
  name: string;
  summary: string;
  cluster_type: string;
  trade_ids: string[];
  trade_count: string;
  avg_return: number;
  win_rate: number;
  total_pnl: number;
  risk_reward_ratio: number;
  pattern_features: Record<string, any>;
  dominant_instrument: string;
  dominant_time_window: string;
  dominant_setup: string;
  dominant_mood: string;
  cluster_score: number;
  analysis_date: string;
  feature_weights: Record<string, number>;
  is_saved_to_playbook: string;
  user_notes?: string;
  user_rating?: string;
  created_at: string;
  updated_at: string;
}

export interface PatternInsights {
  total_patterns: number;
  profitable_patterns: number;
  losing_patterns: number;
  best_pattern: {
    name: string;
    total_pnl: number;
    win_rate: number;
  } | null;
  worst_pattern: {
    name: string;
    total_pnl: number;
    win_rate: number;
  } | null;
  insights: string[];
  time_patterns: Record<string, number[]>;
}

export interface AnalysisStatus {
  status: 'not_started' | 'processing' | 'completed';
  cluster_count: number;
  last_analysis: string | null;
  message: string;
}

class PatternsService {
  async analyzePatterns(minTrades: number = 20): Promise<{
    message: string;
    status: string;
    trade_count: number;
    estimated_time: string;
  }> {
    return apiRequest(`/api/v1/patterns/analyze?min_trades=${minTrades}`, {
      method: 'POST',
    });
  }

  async getAnalysisStatus(): Promise<AnalysisStatus> {
    return apiRequest('/api/v1/patterns/status');
  }

  async getPatternClusters(filters: {
    cluster_type?: string;
    min_avg_return?: number;
    max_avg_return?: number;
    saved_only?: boolean;
    limit?: number;
  } = {}): Promise<PatternCluster[]> {
    const params = new URLSearchParams();
    
    if (filters.cluster_type) params.append('cluster_type', filters.cluster_type);
    if (filters.min_avg_return !== undefined) params.append('min_avg_return', filters.min_avg_return.toString());
    if (filters.max_avg_return !== undefined) params.append('max_avg_return', filters.max_avg_return.toString());
    if (filters.saved_only) params.append('saved_only', 'true');
    if (filters.limit) params.append('limit', filters.limit.toString());

    const queryString = params.toString();
    return apiRequest(`/api/v1/patterns/clusters${queryString ? `?${queryString}` : ''}`);
  }

  async getPatternCluster(clusterId: string): Promise<PatternCluster> {
    return apiRequest(`/api/v1/patterns/clusters/${clusterId}`);
  }

  async updatePatternCluster(clusterId: string, updates: {
    name?: string;
    summary?: string;
    user_notes?: string;
    user_rating?: string;
    is_saved_to_playbook?: string;
  }): Promise<PatternCluster> {
    return apiRequest(`/api/v1/patterns/clusters/${clusterId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
  }

  async deletePatternCluster(clusterId: string): Promise<{ message: string }> {
    return apiRequest(`/api/v1/patterns/clusters/${clusterId}`, {
      method: 'DELETE',
    });
  }

  async getClusterTrades(clusterId: string): Promise<{
    cluster_id: string;
    trades: any[];
  }> {
    return apiRequest(`/api/v1/patterns/clusters/${clusterId}/trades`);
  }

  async getPatternInsights(): Promise<PatternInsights> {
    return apiRequest('/api/v1/patterns/insights');
  }

  async saveToPlaybook(clusterId: string): Promise<{ message: string }> {
    return apiRequest(`/api/v1/patterns/clusters/${clusterId}/save-to-playbook`, {
      method: 'POST',
    });
  }
}

export const patternsService = new PatternsService();
export default patternsService;
