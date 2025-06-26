
import { apiClient } from './api';

export interface PlaybookMetrics {
  playbook_name: string;
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  average_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
  total_pnl: number;
  avg_trade_duration: number;
  largest_win: number;
  largest_loss: number;
  consecutive_wins: number;
  consecutive_losses: number;
}

export interface ComparisonData {
  metrics: PlaybookMetrics[];
  performance_comparison: {
    playbook_name: string;
    monthly_returns: Array<{
      month: string;
      return: number;
    }>;
  }[];
  risk_analysis: {
    playbook_name: string;
    var_95: number;
    var_99: number;
    expected_shortfall: number;
    volatility: number;
  }[];
}

export interface PlaybookOptimization {
  playbook_name: string;
  current_metrics: PlaybookMetrics;
  recommendations: {
    type: 'entry_timing' | 'exit_strategy' | 'risk_management' | 'position_sizing';
    description: string;
    potential_improvement: number;
    confidence: number;
  }[];
  suggested_parameters: {
    parameter: string;
    current_value: any;
    suggested_value: any;
    reasoning: string;
  }[];
}

class PlaybookComparisonService {
  async getAvailablePlaybooks(): Promise<string[]> {
    try {
      const response = await apiClient.get('/analytics/playbooks/available');
      return response.data.playbooks || [];
    } catch (error) {
      console.error('Failed to fetch available playbooks:', error);
      return [];
    }
  }

  async comparePlaybooks(playbookNames: string[]): Promise<ComparisonData> {
    try {
      const response = await apiClient.post('/analytics/playbooks/compare', {
        playbooks: playbookNames
      });
      return response.data;
    } catch (error) {
      console.error('Failed to compare playbooks:', error);
      throw error;
    }
  }

  async getPlaybookOptimization(playbookName: string): Promise<PlaybookOptimization> {
    try {
      const response = await apiClient.get(`/analytics/playbooks/${playbookName}/optimization`);
      return response.data;
    } catch (error) {
      console.error('Failed to get playbook optimization:', error);
      throw error;
    }
  }

  async getPlaybookPerformanceOverTime(playbookName: string, period: string = '6M'): Promise<{
    dates: string[];
    cumulative_returns: number[];
    drawdown: number[];
    trade_frequency: number[];
  }> {
    try {
      const response = await apiClient.get(`/analytics/playbooks/${playbookName}/performance`, {
        params: { period }
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get playbook performance over time:', error);
      throw error;
    }
  }

  async getPlaybookRiskMetrics(playbookName: string): Promise<{
    var_95: number;
    var_99: number;
    expected_shortfall: number;
    volatility: number;
    beta: number;
    alpha: number;
    information_ratio: number;
    calmar_ratio: number;
  }> {
    try {
      const response = await apiClient.get(`/analytics/playbooks/${playbookName}/risk`);
      return response.data;
    } catch (error) {
      console.error('Failed to get playbook risk metrics:', error);
      throw error;
    }
  }

  async exportComparison(playbookNames: string[], format: 'pdf' | 'excel' = 'pdf'): Promise<Blob> {
    try {
      const response = await apiClient.post('/analytics/playbooks/export', {
        playbooks: playbookNames,
        format
      }, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('Failed to export comparison:', error);
      throw error;
    }
  }
}

export const playbookComparisonService = new PlaybookComparisonService();
