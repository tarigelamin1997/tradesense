
import { api } from './api';

export interface Portfolio {
  id: string;
  name: string;
  initial_balance: number;
  current_balance: number;
  total_pnl: number;
  total_trades: number;
  winning_trades: number;
  win_rate: number;
  is_default: boolean;
  created_at: string;
  return_percentage: number;
}

export interface CreatePortfolioRequest {
  name: string;
  initial_balance: number;
}

export interface EquityDataPoint {
  date: string;
  balance: number;
  daily_pnl: number;
  total_pnl: number;
  trade_count: number;
}

export interface EquityMetrics {
  sharpe_ratio: number;
  max_drawdown: number;
  total_return: number;
}

export interface EquityCurveResponse {
  success: boolean;
  equity_curve: EquityDataPoint[];
  metrics: EquityMetrics;
}

export const portfolioService = {
  async createPortfolio(data: CreatePortfolioRequest): Promise<any> {
    const response = await api.post('/portfolio/', data);
    return response.data;
  },

  async getPortfolios(): Promise<Portfolio[]> {
    const response = await api.get('/portfolio/');
    return response.data;
  },

  async simulateTrades(portfolioId: string, tradeIds: string[]): Promise<any> {
    const response = await api.post(`/portfolio/${portfolioId}/simulate`, tradeIds);
    return response.data;
  },

  async getEquityCurve(portfolioId: string): Promise<EquityCurveResponse> {
    const response = await api.get(`/portfolio/${portfolioId}/equity-curve`);
    return response.data;
  },

  async deletePortfolio(portfolioId: string): Promise<any> {
    const response = await api.delete(`/portfolio/${portfolioId}`);
    return response.data;
  }
};
