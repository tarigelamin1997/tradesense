
import { api } from './api';

export interface PortfolioCreate {
  name: string;
  initial_balance: number;
}

export interface Portfolio {
  id: string;
  name: string;
  initial_balance: number;
  current_balance: number;
  total_pnl: number;
  total_trades: number;
  winning_trades: number;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface EquityPoint {
  timestamp: string;
  balance: number;
  daily_pnl: number;
  total_pnl: number;
  trade_count: number;
}

export interface TradeSimulation {
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  entry_price: number;
  exit_price?: number;
  entry_time: string;
  exit_time?: string;
  strategy?: string;
  notes?: string;
}

export interface PortfolioCreateResponse {
  success: boolean;
  portfolio?: Portfolio;
  error?: string;
}

export const portfolioService = {
  async createPortfolio(data: PortfolioCreate): Promise<PortfolioCreateResponse> {
    try {
      const response = await api.post('/portfolio/', data);
      return response.data;
    } catch (error) {
      console.error('Create portfolio error:', error);
      throw error;
    }
  },

  async getPortfolios(): Promise<Portfolio[]> {
    try {
      const response = await api.get('/portfolio/');
      return response.data;
    } catch (error) {
      console.error('Get portfolios error:', error);
      throw error;
    }
  },

  async getPortfolio(portfolioId: string): Promise<Portfolio> {
    try {
      const response = await api.get(`/portfolio/${portfolioId}`);
      return response.data;
    } catch (error) {
      console.error('Get portfolio error:', error);
      throw error;
    }
  },

  async updatePortfolio(portfolioId: string, data: Partial<Portfolio>): Promise<Portfolio> {
    try {
      const response = await api.put(`/portfolio/${portfolioId}`, data);
      return response.data;
    } catch (error) {
      console.error('Update portfolio error:', error);
      throw error;
    }
  },

  async deletePortfolio(portfolioId: string): Promise<void> {
    try {
      await api.delete(`/portfolio/${portfolioId}`);
    } catch (error) {
      console.error('Delete portfolio error:', error);
      throw error;
    }
  },

  async getEquityCurve(portfolioId: string): Promise<EquityPoint[]> {
    try {
      const response = await api.get(`/portfolio/${portfolioId}/equity-curve`);
      return response.data;
    } catch (error) {
      console.error('Get equity curve error:', error);
      throw error;
    }
  },

  async simulateTrade(portfolioId: string, tradeData: TradeSimulation): Promise<any> {
    try {
      const response = await api.post(`/portfolio/${portfolioId}/simulate-trade`, tradeData);
      return response.data;
    } catch (error) {
      console.error('Simulate trade error:', error);
      throw error;
    }
  },

  async getPortfolioStats(portfolioId: string): Promise<any> {
    try {
      const response = await api.get(`/portfolio/${portfolioId}/stats`);
      return response.data;
    } catch (error) {
      console.error('Get portfolio stats error:', error);
      throw error;
    }
  },

  async resetPortfolio(portfolioId: string): Promise<Portfolio> {
    try {
      const response = await api.post(`/portfolio/${portfolioId}/reset`);
      return response.data;
    } catch (error) {
      console.error('Reset portfolio error:', error);
      throw error;
    }
  },

  async backtest(portfolioId: string, trades: TradeSimulation[]): Promise<any> {
    try {
      const response = await api.post(`/portfolio/${portfolioId}/backtest`, { trades });
      return response.data;
    } catch (error) {
      console.error('Backtest error:', error);
      throw error;
    }
  }
};
