
import { api } from './api';

export interface ConfidenceBin {
  confidence_range: string;
  confidence_midpoint: number;
  total_trades: number;
  win_rate: number;
  avg_pnl: number;
  median_pnl: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  total_pnl: number;
  std_dev: number;
}

export interface OverallConfidenceStats {
  avg_confidence: number;
  median_confidence: number;
  confidence_std: number;
  confidence_distribution: Record<string, number>;
  confidence_pnl_correlation: number;
  correlation_interpretation: string;
}

export interface ConfidenceCalibrationResponse {
  calibration_data: ConfidenceBin[];
  insights: string[];
  overall_stats: OverallConfidenceStats;
  total_trades_analyzed: number;
}

export interface PlaybookConfidenceData {
  total_trades: number;
  avg_confidence: number;
  avg_pnl: number;
  calibration_data: ConfidenceBin[];
}

export const confidenceCalibrationService = {
  async getConfidenceCalibration(): Promise<ConfidenceCalibrationResponse> {
    const response = await api.get('/trades/confidence-calibration');
    return response.data;
  },

  async getConfidenceCalibrationByPlaybook(): Promise<Record<string, PlaybookConfidenceData>> {
    const response = await api.get('/trades/confidence-calibration/by-playbook');
    return response.data;
  }
};
