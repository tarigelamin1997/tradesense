export interface User {
  user_id: string;
  email: string;
  created_at: string;
}

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

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export type TradeDirection = 'long' | 'short';
export type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';
export type AnalysisStatus = 'idle' | 'analyzing' | 'success' | 'error';