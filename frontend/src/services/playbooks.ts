
import { api } from './api';

export interface Playbook {
  id: string;
  user_id: string;
  name: string;
  entry_criteria: string;
  exit_criteria: string;
  description?: string;
  status: 'active' | 'archived';
  total_trades: string;
  win_rate: string;
  avg_pnl: string;
  total_pnl: string;
  created_at: string;
  updated_at: string;
}

export interface PlaybookCreate {
  name: string;
  entry_criteria: string;
  exit_criteria: string;
  description?: string;
  status?: 'active' | 'archived';
}

export interface PlaybookUpdate {
  name?: string;
  entry_criteria?: string;
  exit_criteria?: string;
  description?: string;
  status?: 'active' | 'archived';
}

export interface PlaybookAnalytics {
  id: string;
  name: string;
  total_trades: number;
  win_rate: number;
  avg_pnl: number;
  total_pnl: number;
  avg_hold_time_minutes?: number;
  best_win?: number;
  worst_loss?: number;
  consecutive_wins: number;
  consecutive_losses: number;
  recommendation: 'focus_more' | 'reduce_size' | 'cut_play' | 'keep_current' | 'insufficient_data';
  performance_trend: 'improving' | 'declining' | 'stable' | 'insufficient_data';
}

export const playbooksService = {
  async createPlaybook(data: PlaybookCreate): Promise<Playbook> {
    const response = await api.post('/playbooks/', data);
    return response.data;
  },

  async getPlaybooks(params?: {
    status?: string;
    sort_by?: string;
    sort_order?: string;
    limit?: number;
  }): Promise<Playbook[]> {
    const response = await api.get('/playbooks/', { params });
    return response.data;
  },

  async getPlaybook(id: string): Promise<Playbook> {
    const response = await api.get(`/playbooks/${id}`);
    return response.data;
  },

  async updatePlaybook(id: string, data: PlaybookUpdate): Promise<Playbook> {
    const response = await api.put(`/playbooks/${id}`, data);
    return response.data;
  },

  async deletePlaybook(id: string): Promise<void> {
    await api.delete(`/playbooks/${id}`);
  },

  async archivePlaybook(id: string): Promise<void> {
    await api.post(`/playbooks/${id}/archive`);
  },

  async activatePlaybook(id: string): Promise<void> {
    await api.post(`/playbooks/${id}/activate`);
  },

  async getPlaybookAnalytics(params?: {
    min_trades?: number;
    include_archived?: boolean;
  }): Promise<PlaybookAnalytics[]> {
    const response = await api.get('/playbooks/analytics/summary', { params });
    return response.data;
  },

  async getPlaybookTrades(id: string, limit?: number): Promise<any> {
    const response = await api.get(`/playbooks/${id}/trades`, {
      params: { limit }
    });
    return response.data;
  },

  async refreshStats(): Promise<void> {
    await api.post('/playbooks/refresh-stats');
  }
};
import { api } from './api';

export interface Playbook {
  id: string;
  user_id: string;
  name: string;
  entry_criteria: string;
  exit_criteria: string;
  description?: string;
  status: 'active' | 'archived';
  created_at: string;
  updated_at?: string;
}

export interface PlaybookCreate {
  name: string;
  entry_criteria: string;
  exit_criteria: string;
  description?: string;
  status?: 'active' | 'archived';
}

export interface PlaybookUpdate {
  name?: string;
  entry_criteria?: string;
  exit_criteria?: string;
  description?: string;
  status?: 'active' | 'archived';
}

export interface PlaybookPerformance {
  playbook_id: string;
  playbook_name: string;
  trade_count: number;
  total_pnl: number;
  avg_pnl: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  avg_hold_time_minutes?: number;
  profit_factor?: number;
}

export interface PlaybookAnalytics {
  playbooks: PlaybookPerformance[];
  summary: {
    total_playbooks: number;
    total_trades: number;
    total_pnl: number;
    best_performing?: string;
    most_active?: string;
  };
}

export const playbooksApi = {
  // Create a new playbook
  createPlaybook: (data: PlaybookCreate): Promise<Playbook> =>
    api.post('/playbooks', data),

  // Get all playbooks
  getPlaybooks: (includeArchived = false): Promise<Playbook[]> =>
    api.get(`/playbooks?include_archived=${includeArchived}`),

  // Get a specific playbook
  getPlaybook: (id: string): Promise<Playbook> =>
    api.get(`/playbooks/${id}`),

  // Update a playbook
  updatePlaybook: (id: string, data: PlaybookUpdate): Promise<Playbook> =>
    api.put(`/playbooks/${id}`, data),

  // Delete (archive) a playbook
  deletePlaybook: (id: string): Promise<void> =>
    api.delete(`/playbooks/${id}`),

  // Get playbook analytics
  getPlaybookAnalytics: (days?: number): Promise<PlaybookAnalytics> =>
    api.get(`/playbooks/analytics${days ? `?days=${days}` : ''}`),

  // Attach playbook to trade
  attachPlaybookToTrade: (tradeId: string, playbookId?: string): Promise<any> =>
    api.put(`/trades/${tradeId}/playbook`, { playbook_id: playbookId }),
};
