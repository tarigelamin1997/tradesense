
import { api } from './api';

export interface SimulationFilters {
  playbook_ids?: string[];
  exclude_playbook_ids?: string[];
  confidence_score_min?: number;
  confidence_score_max?: number;
  entry_time_start?: string;
  entry_time_end?: string;
  symbols?: string[];
  directions?: string[];
  tags_include?: string[];
  tags_exclude?: string[];
  min_hold_time_minutes?: number;
  max_hold_time_minutes?: number;
  pnl_min?: number;
  pnl_max?: number;
}

export interface SimulationRequest {
  filters: SimulationFilters;
  name?: string;
  compare_to_baseline?: boolean;
}

export interface PerformanceMetrics {
  total_trades: number;
  completed_trades: number;
  total_pnl: number;
  avg_pnl: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  profit_factor?: number;
  sharpe_ratio?: number;
  max_drawdown: number;
  consecutive_wins: number;
  consecutive_losses: number;
  avg_hold_time_minutes?: number;
  best_trade: number;
  worst_trade: number;
}

export interface ComparisonMetrics {
  pnl_difference: number;
  pnl_improvement_pct: number;
  win_rate_difference: number;
  profit_factor_difference?: number;
  avg_pnl_difference: number;
  trade_count_difference: number;
}

export interface SimulationResponse {
  scenario_name?: string;
  filters_applied: SimulationFilters;
  simulation_metrics: PerformanceMetrics;
  baseline_metrics?: PerformanceMetrics;
  comparison?: ComparisonMetrics;
  filtered_trades: any[];
  insights: string[];
  recommendations: string[];
}

export interface PlaybookPerformanceComparison {
  playbook_id?: string;
  playbook_name: string;
  metrics: PerformanceMetrics;
  trade_count: number;
}

export interface WhatIfScenario {
  scenario_name: string;
  description: string;
  metrics: PerformanceMetrics;
  improvement_pct: number;
}

export const strategyLabService = {
  // Run a strategy simulation
  async runSimulation(request: SimulationRequest): Promise<SimulationResponse> {
    const response = await api.post('/strategy-lab/simulate', request);
    return response.data;
  },

  // Compare playbook performance
  async comparePlaybooks(): Promise<PlaybookPerformanceComparison[]> {
    const response = await api.get('/strategy-lab/playbook-comparison');
    return response.data;
  },

  // Get what-if scenarios
  async getWhatIfScenarios(): Promise<WhatIfScenario[]> {
    const response = await api.get('/strategy-lab/what-if-scenarios');
    return response.data;
  },

  // Run multiple simulations in batch
  async batchSimulate(scenarios: SimulationRequest[]): Promise<any> {
    const response = await api.post('/strategy-lab/batch-simulate', scenarios);
    return response.data;
  },

  // Helper method to create common filter presets
  getFilterPresets(): { [key: string]: SimulationFilters } {
    return {
      'High Confidence Only': {
        confidence_score_min: 8
      },
      'No Emotional Trading': {
        tags_exclude: ['fomo', 'revenge', 'greedy', 'fearful', 'impulsive', 'frustrated']
      },
      'Morning Trades Only': {
        entry_time_start: '09:30:00',
        entry_time_end: '11:00:00'
      },
      'Long Positions Only': {
        directions: ['long']
      },
      'Short Positions Only': {
        directions: ['short']
      },
      'Quick Scalps': {
        max_hold_time_minutes: 30
      },
      'Swing Trades': {
        min_hold_time_minutes: 60
      },
      'Profitable Only': {
        pnl_min: 0.01
      }
    };
  }
};

export default strategyLabService;
