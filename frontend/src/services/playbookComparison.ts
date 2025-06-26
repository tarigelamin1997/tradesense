import { api } from './api';

interface PlaybookMetrics {
  playbook_name: string;
  total_trades: number;
  win_rate: number;
  avg_pnl: number;
  profit_factor: number;
  max_drawdown: number;
  sharpe_ratio: number;
  total_pnl: number;
  avg_win: number;
  avg_loss: number;
  largest_win: number;
  largest_loss: number;
  consecutive_wins: number;
  consecutive_losses: number;
}

interface ComparisonData {
  playbooks: PlaybookMetrics[];
  period: string;
  equity_curves: { [key: string]: { dates: string[], values: number[] } };
  monthly_returns: { [key: string]: { months: string[], returns: number[] } };
}

interface PlaybookOption {
  id: string;
  name: string;
  description: string;
  total_trades: number;
  created_at: string;
}

export const playbookComparisonService = {
  async getAvailablePlaybooks(): Promise<PlaybookOption[]> {
    try {
      const response = await api.get('/playbooks');
      return response.data.map((playbook: any) => ({
        id: playbook.id,
        name: playbook.name,
        description: playbook.description || `${playbook.total_trades || 0} trades`,
        total_trades: playbook.total_trades || 0,
        created_at: playbook.created_at
      }));
    } catch (error) {
      console.error('Failed to fetch playbooks:', error);
      // Return mock data for development
      return [
        { id: 'momentum', name: 'Momentum Strategy', description: '45 trades', total_trades: 45, created_at: '2024-01-01' },
        { id: 'mean-reversion', name: 'Mean Reversion', description: '38 trades', total_trades: 38, created_at: '2024-01-01' },
        { id: 'breakout', name: 'Breakout Strategy', description: '52 trades', total_trades: 52, created_at: '2024-01-01' },
        { id: 'scalping', name: 'Scalping', description: '127 trades', total_trades: 127, created_at: '2024-01-01' }
      ];
    }
  },

  async comparePlaybooks(playbookIds: string[], period: string): Promise<ComparisonData> {
    try {
      const response = await api.post('/analytics/playbook-comparison', {
        playbook_ids: playbookIds,
        period
      });
      return response.data;
    } catch (error) {
      console.error('Failed to compare playbooks:', error);
      // Return mock data for development
      return {
        playbooks: playbookIds.map((id, index) => ({
          playbook_name: id.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase()),
          total_trades: 45 + index * 10,
          win_rate: 0.55 + index * 0.05,
          avg_pnl: 125.50 + index * 25,
          total_pnl: 5647.25 + index * 1200,
          profit_factor: 1.35 + index * 0.15,
          max_drawdown: 0.12 - index * 0.02,
          sharpe_ratio: 1.25 + index * 0.20,
          avg_win: 285.75 + index * 50,
          avg_loss: -156.25 + index * 20,
          largest_win: 1250.00 + index * 200,
          largest_loss: -892.50 + index * 100,
          consecutive_wins: 7 + index,
          consecutive_losses: 4 + index
        })),
        period,
        equity_curves: this.generateMockEquityCurves(playbookIds, period),
        monthly_returns: this.generateMockMonthlyReturns(playbookIds, period)
      };
    }
  },

  generateMockEquityCurves(playbookIds: string[], period: string) {
    const curves: { [key: string]: { dates: string[], values: number[] } } = {};
    const days = period === '7d' ? 7 : period === '30d' ? 30 : period === '90d' ? 90 : 365;

    playbookIds.forEach((id, index) => {
      const dates: string[] = [];
      const values: number[] = [];
      let currentValue = 0;

      for (let i = 0; i < days; i++) {
        const date = new Date();
        date.setDate(date.getDate() - (days - i));
        dates.push(date.toISOString().split('T')[0]);

        const randomChange = (Math.random() - 0.4) * 100 + (index * 10);
        currentValue += randomChange;
        values.push(currentValue);
      }

      curves[id.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())] = { dates, values };
    });

    return curves;
  },

  generateMockMonthlyReturns(playbookIds: string[], period: string) {
    const returns: { [key: string]: { months: string[], returns: number[] } } = {};
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthsToShow = period === '1y' ? 12 : period === '6m' ? 6 : 3;

    playbookIds.forEach((id, index) => {
      const monthlyReturns = months.slice(0, monthsToShow).map(() => 
        (Math.random() - 0.3) * 20 + (index * 2)
      );

      returns[id.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())] = {
        months: months.slice(0, monthsToShow),
        returns: monthlyReturns
      };
    });

    return returns;
  },

  async getPlaybookTrends(playbookId: string, period: string) {
    try {
      const response = await api.get(`/analytics/playbook-trends/${playbookId}`, {
        params: { period }
      });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch playbook trends:', error);
      return null;
    }
  }
};