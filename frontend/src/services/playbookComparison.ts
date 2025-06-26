
import { api } from './api';

export interface PlaybookComparisonData {
  playbook_id: string;
  playbook_name: string;
  description?: string;
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  expectancy: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_pnl: number;
  avg_win: number;
  avg_loss: number;
  max_consecutive_wins: number;
  max_consecutive_losses: number;
  monthly_performance: Array<{
    month: string;
    pnl: number;
    trades: number;
  }>;
  risk_adjusted_return: number;
  win_rate_rank?: number;
  profit_factor_rank?: number;
  expectancy_rank?: number;
  sharpe_ratio_rank?: number;
  total_pnl_rank?: number;
}

export interface PlaybookComparisonResponse {
  comparison_data: PlaybookComparisonData[];
  summary: {
    total_playbooks: number;
    date_range: {
      start: string | null;
      end: string | null;
    };
    best_performer: string | null;
  };
}

export interface CorrelationMatrixResponse {
  correlation_matrix: Record<string, Record<string, number>>;
  playbook_ids: string[];
  message?: string;
}

export interface PerformanceOverTimeData {
  performance_data: Record<string, {
    playbook_name: string;
    performance: Array<{
      period: string;
      pnl: number;
      cumulative_pnl: number;
      trade_count: number;
      avg_pnl: number;
    }>;
  }>;
  period: string;
}

export const playbookComparisonService = {
  comparePlaybooks: async (
    playbookIds: string[],
    startDate?: string,
    endDate?: string
  ): Promise<PlaybookComparisonResponse> => {
    const params = new URLSearchParams();
    playbookIds.forEach(id => params.append('playbook_ids', id));
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await api.get(`/api/v1/analytics/playbook_comparison/compare?${params}`);
    return response.data;
  },

  getCorrelationMatrix: async (playbookIds: string[]): Promise<CorrelationMatrixResponse> => {
    const params = new URLSearchParams();
    playbookIds.forEach(id => params.append('playbook_ids', id));

    const response = await api.get(`/api/v1/analytics/playbook_comparison/correlation-matrix?${params}`);
    return response.data;
  },

  getPerformanceOverTime: async (
    playbookIds: string[],
    period: 'daily' | 'weekly' | 'monthly' = 'daily'
  ): Promise<PerformanceOverTimeData> => {
    const params = new URLSearchParams();
    playbookIds.forEach(id => params.append('playbook_ids', id));
    params.append('period', period);

    const response = await api.get(`/api/v1/analytics/playbook_comparison/performance-over-time?${params}`);
    return response.data;
  }
};
