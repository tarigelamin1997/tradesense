
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

class JournalService {
  private getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async createJournalEntry(tradeId: string, entryData: JournalEntryCreate): Promise<JournalEntry> {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/trades/${tradeId}/journal`,
      entryData,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async getTradeJournalEntries(tradeId: string): Promise<JournalEntry[]> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/trades/${tradeId}/journal`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async updateJournalEntry(entryId: string, updateData: JournalEntryUpdate): Promise<JournalEntry> {
    const response = await axios.put(
      `${API_BASE_URL}/api/v1/journal/${entryId}`,
      updateData,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async deleteJournalEntry(entryId: string): Promise<void> {
    await axios.delete(
      `${API_BASE_URL}/api/v1/journal/${entryId}`,
      { headers: this.getAuthHeaders() }
    );
  }

  async getJournalEntry(entryId: string): Promise<JournalEntry> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/journal/${entryId}`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async getAllJournalEntries(limit: number = 100, offset: number = 0): Promise<JournalEntry[]> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/journal?limit=${limit}&offset=${offset}`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async getTradeWithJournal(tradeId: string): Promise<TradeWithJournal> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/trades/${tradeId}`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }
}

export const journalService = new JournalService();
