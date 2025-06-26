
import { api } from './api';

export interface ExecutionMetrics {
  trade_id: string;
  symbol: string;
  entry_time: string;
  exit_time: string;
  pnl: number;
  entry_timing_score: number;
  exit_quality_score: number;
  slippage_cost: number;
  regret_index: number;
  execution_score: number;
  execution_grade: string;
  primary_weakness: string;
}

export interface ExecutionSummary {
  total_trades_analyzed: number;
  average_execution_score: number;
  average_entry_score: number;
  average_exit_score: number;
  average_regret_index: number;
  execution_consistency: number;
  grade_distribution: Record<string, number>;
  top_quartile_threshold: number;
  bottom_quartile_threshold: number;
}

export interface ExecutionQualityAnalysis {
  trade_execution_data: ExecutionMetrics[];
  execution_summary: ExecutionSummary;
  insights: string[];
  recommendations: string[];
}

export const executionQualityService = {
  getExecutionQuality: async (): Promise<ExecutionQualityAnalysis> => {
    const response = await api.get('/trades/execution-quality');
    return response.data;
  }
};
