import { api } from './client';

export interface JournalEntry {
  id: number;
  title: string;
  content: string;
  mood: string;
  confidence: number;
  tags: string[];
  trade_ids?: number[];
  created_at: string;
  updated_at: string;
}

export interface CreateJournalEntry {
  title: string;
  content: string;
  mood: string;
  confidence: number;
  tags: string[];
  trade_ids?: number[];
}

export interface UpdateJournalEntry {
  title?: string;
  content?: string;
  mood?: string;
  confidence?: number;
  tags?: string[];
  trade_ids?: number[];
}

export const journalApi = {
  // Get all journal entries
  async getEntries(): Promise<JournalEntry[]> {
    try {
      const response = await api.get<{ entries: JournalEntry[] }>('/api/v1/journal/entries');
      return response.entries || [];
    } catch (error) {
      console.error('Failed to fetch journal entries:', error);
      return [];
    }
  },

  // Get a single journal entry
  async getEntry(id: number): Promise<JournalEntry> {
    return api.get<JournalEntry>(`/api/v1/journal/entries/${id}`);
  },

  // Create a new journal entry
  async createEntry(data: CreateJournalEntry): Promise<JournalEntry> {
    return api.post<JournalEntry>('/api/v1/journal/entries', data);
  },

  // Update an existing journal entry
  async updateEntry(id: number, data: UpdateJournalEntry): Promise<JournalEntry> {
    return api.put<JournalEntry>(`/api/v1/journal/entries/${id}`, data);
  },

  // Delete a journal entry
  async deleteEntry(id: number): Promise<void> {
    await api.delete<void>(`/api/v1/journal/entries/${id}`);
  },

  // Get journal insights
  async getInsights(): Promise<any> {
    return api.get<any>('/api/v1/journal/insights');
  }
};