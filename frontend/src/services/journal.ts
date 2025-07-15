import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface JournalEntry {
  id: string;
  trade_id?: string;
  user_id: string;
  title: string;
  content: string;
  mood?: string;
  timestamp: string;
  created_at: string;
  updated_at: string;
}

export interface JournalEntryCreate {
  title: string;
  content: string;
  mood?: string;
}

export interface JournalEntryUpdate {
  title?: string;
  content?: string;
  mood?: string;
}

export interface TradeWithJournal {
  id: string;
  symbol: string;
  direction: string;
  quantity: number;
  entry_price: number;
  exit_price?: number;
  entry_time: string;
  exit_time?: string;
  pnl?: number;
  strategy_tag?: string;
  notes?: string;
  journal_entries: JournalEntry[];
  created_at: string;
  updated_at: string;
}


const getAuthHeaders = () => {
  const token = localStorage.getItem('authToken');
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
};

export const journalService = {

  // Get all journal entries (used by Journal component)
  async getJournalEntries(limit: number = 100, offset: number = 0): Promise<JournalEntry[]> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/journal`, {
      params: { limit, offset },
      headers: getAuthHeaders()
    });
    return response.data;
  },

  // Create a new journal entry (general, not tied to a trade)
  async createJournalEntry(data: JournalEntryCreate): Promise<JournalEntry> {
    const response = await axios.post(`${API_BASE_URL}/api/v1/journal`, data, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  // Delete a journal entry
  async deleteJournalEntry(entryId: string): Promise<void> {
    await axios.delete(`${API_BASE_URL}/api/v1/journal/${entryId}`, {
      headers: getAuthHeaders()
    });
  },

  // Get trades with journal entries
  async getTradesWithJournal(): Promise<TradeWithJournal[]> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/trades/with-journal`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  // Create journal entry for a specific trade
  async createTradeJournalEntry(tradeId: string, data: JournalEntryCreate): Promise<JournalEntry> {
    const response = await axios.post(`${API_BASE_URL}/api/v1/trades/${tradeId}/journal`, data, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  // Get all journal entries for a trade
  async getTradeJournalEntries(tradeId: string): Promise<JournalEntry[]> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/trades/${tradeId}/journal`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  // Update journal entry
  async updateJournalEntry(entryId: string, data: JournalEntryUpdate): Promise<JournalEntry> {
    const response = await axios.put(`${API_BASE_URL}/api/v1/journal/${entryId}`, data, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  // Get specific journal entry
  async getJournalEntry(entryId: string): Promise<JournalEntry> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/journal/${entryId}`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  // Psychology analytics
  async getEmotionAnalytics(startDate?: string, endDate?: string): Promise<any> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/journal/analytics/emotions`, {
      params: { start_date: startDate, end_date: endDate },
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async getPsychologyInsights(): Promise<any> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/journal/analytics/psychology`, {
      headers: getAuthHeaders()
    });
    return response.data;
  }
};