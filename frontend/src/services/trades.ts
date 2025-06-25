
import { apiClient } from './api';

export interface Trade {
  id: string;
  symbol: string;
  entry_time: string;
  exit_time: string;
  direction: 'long' | 'short';
  quantity: number;
  entry_price: number;
  exit_price: number;
  pnl: number;
}

export interface Analytics {
  total_trades: number;
  total_pnl: number;
  win_rate: number;
  profit_factor: number;
  max_drawdown: number;
  sharpe_ratio: number;
  best_day: number;
  worst_day: number;
  avg_daily_pnl: number;
  risk_reward_ratio: number;
  equity_curve: Array<{ date: string; cumulativePnL: number }>;
  pnl_distribution: Array<{ range: string; count: number }>;
  symbol_breakdown: Array<{
    name: string;
    trades: number;
    winRate: number;
    pnl: number;
  }>;
}

export interface UploadResponse {
  success: boolean;
  data?: Trade[];
  message?: string;
}

export const tradesService = {
  async uploadTrades(formData: FormData, onProgress?: (progress: number) => void): Promise<UploadResponse> {
    const response = await apiClient.uploadFile<UploadResponse>('/trades/upload', formData, onProgress);
    return response.data;
  },

  async getTrades(): Promise<Trade[]> {
    const response = await apiClient.get<Trade[]>('/trades');
    return response.data;
  },

  async getAnalytics(): Promise<Analytics> {
    const response = await apiClient.get<Analytics>('/analytics/dashboard');
    return response.data;
  },

  async analyzeTrades(trades: Trade[]): Promise<Analytics> {
    const response = await apiClient.post<Analytics>('/analytics/analyze', { trades });
    return response.data;
  },
};
