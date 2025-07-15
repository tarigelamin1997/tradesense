
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
  getExecutionQuality: async (): Promise<ExecutionQualityResponse> => {
    const response = await api.get('/trades/execution-quality');
    return response.data;
  }
};

export interface ExecutionQualityMetrics {
  entry_score: number;
  exit_score: number;
  slippage: number;
  regret_index: number;
  holding_efficiency: number;
  execution_score: number;
  execution_grade: string;
}

export interface TradeExecutionData {
  trade_id: string;
  symbol: string;
  entry_time: string;
  exit_time: string;
  pnl: number;
  direction: string;
  playbook_id?: string;
  entry_score: number;
  exit_score: number;
  slippage: number;
  regret_index: number;
  holding_efficiency: number;
  execution_score: number;
  execution_grade: string;
}

export interface OverallExecutionStats {
  avg_execution_score: number;
  execution_score_std: number;
  avg_entry_score: number;
  avg_exit_score: number;
  excellent_executions: number;
  poor_executions: number;
  grade_distribution: { [grade: string]: number };
}

export interface PlaybookExecutionStats {
  [playbook_id: string]: {
    total_trades: number;
    avg_execution_score: number;
    avg_pnl: number;
    win_rate: number;
  };
}

// For market execution quality dashboard
export interface SummaryData {
  avg_fill_rate: number;
  avg_slippage: number;
  avg_price_impact: number;
  total_trades: number;
}

export interface PriceImpactBySize {
  size_category: string;
  avg_impact: number;
  trade_count: number;
}

export interface TimingAnalysis {
  hour: number;
  avg_fill_time: number;
  avg_slippage: number;
}

export interface VenueAnalysis {
  venue: string;
  trade_count: number;
  percentage: number;
  avg_fill_rate: number;
  avg_slippage: number;
  avg_fill_time: number;
}

export interface SlippagePattern {
  volume: number;
  slippage: number;
}

export interface ExecutionQualityResponse {
  total_trades_analyzed: number;
  overall_stats: OverallExecutionStats;
  trade_execution_data: TradeExecutionData[];
  playbook_analysis: PlaybookExecutionStats;
  insights: string[];
  generated_at: string;
  // Additional fields for ExecutionQualityDashboard
  summary: SummaryData;
  price_impact_by_size: PriceImpactBySize[];
  timing_analysis: TimingAnalysis[];
  venue_analysis: VenueAnalysis[];
  slippage_patterns: SlippagePattern[];
}
