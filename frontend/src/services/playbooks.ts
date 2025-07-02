import { api } from './api';

export interface Playbook {
  id: string;
  name: string;
  description?: string;
  criteria: string[];
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface PlaybookAnalytics {
  playbook_id: string;
  total_trades: number;
  win_rate: number;
  avg_return: number;
  total_pnl: number;
  sharpe_ratio: number;
  max_drawdown: number;
}

export interface PlaybookComparison {
  playbooks: Array<{
    playbook_id: string;
    playbook_name: string;
    total_trades: number;
    win_rate: number;
    avg_return: number;
    total_pnl: number;
    sharpe_ratio: number;
    max_drawdown: number;
    profit_factor: number;
    expectancy: number;
    avg_win: number;
    avg_loss: number;
    largest_win: number;
    largest_loss: number;
  }>;
  comparison_matrix: Array<{
    metric: string;
    values: { [playbook_name: string]: number };
  }>;
}

class PlaybooksService {
  async getPlaybooks(): Promise<Playbook[]> {
    const response = await api.get('/playbooks');
    return response.data;
  }

  async createPlaybook(playbook: Omit<Playbook, 'id' | 'user_id' | 'created_at' | 'updated_at'>): Promise<Playbook> {
    const response = await api.post('/playbooks', playbook);
    return response.data;
  }

  async updatePlaybook(id: string, updates: Partial<Playbook>): Promise<Playbook> {
    const response = await api.put(`/playbooks/${id}`, updates);
    return response.data;
  }

  async deletePlaybook(id: string): Promise<void> {
    await api.delete(`/playbooks/${id}`);
  }

  async getPlaybookAnalytics(playbookId: string): Promise<PlaybookAnalytics> {
    const response = await api.get(`/playbooks/${playbookId}/analytics`);
    return response.data;
  }

  async comparePlaybooks(playbookIds: string[]): Promise<PlaybookComparison> {
    const response = await api.post('/analytics/playbook-comparison', {
      playbook_ids: playbookIds
    });
    return response.data;
  }

  async getPlaybookTrades(playbookId: string) {
    const response = await api.get(`/playbooks/${playbookId}/trades`);
    return response.data;
  }
}

export const playbooksService = new PlaybooksService();