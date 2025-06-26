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

export const playbooksService = {
  // Create a new playbook
  createPlaybook: async (data: PlaybookCreate): Promise<Playbook> => {
    const response = await api.post('/playbooks/', data);
    return response.data;
  },

  // Get all playbooks
  getPlaybooks: async (includeArchived = false): Promise<Playbook[]> => {
    const response = await api.get(`/playbooks/?include_archived=${includeArchived}`);
    return response.data;
  },

  // Get a specific playbook
  getPlaybook: async (id: string): Promise<Playbook> => {
    const response = await api.get(`/playbooks/${id}`);
    return response.data;
  },

  // Update a playbook
  updatePlaybook: async (id: string, data: PlaybookUpdate): Promise<Playbook> => {
    const response = await api.put(`/playbooks/${id}`, data);
    return response.data;
  },

  // Delete (archive) a playbook
  deletePlaybook: async (id: string): Promise<void> => {
    await api.delete(`/playbooks/${id}`);
  },

  // Get playbook analytics
  getPlaybookAnalytics: async (days?: number): Promise<PlaybookAnalytics> => {
    const response = await api.get(`/playbooks/analytics${days ? `?days=${days}` : ''}`);
    return response.data;
  },

  // Attach playbook to trade
  attachPlaybookToTrade: async (tradeId: string, playbookId?: string): Promise<any> => {
    const response = await api.put(`/trades/${tradeId}/playbook`, { playbook_id: playbookId });
    return response.data;
  },
};