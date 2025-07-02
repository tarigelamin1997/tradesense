
import { api } from './api';

export interface MentalMapEntry {
  id: string;
  user_id: string;
  trade_id?: string;
  session_id?: string;
  timestamp: string;
  note: string;
  mood: string;
  confidence_score?: string;
  checklist_flags?: string[];
  screenshot_url?: string;
  chart_context?: string;
  created_at: string;
  updated_at: string;
}

export interface MentalMapEntryCreate {
  trade_id?: string;
  session_id?: string;
  timestamp: string;
  note: string;
  mood: string;
  confidence_score?: string;
  checklist_flags?: string[];
  screenshot_url?: string;
  chart_context?: string;
}

export interface SessionReplay {
  id: string;
  user_id: string;
  start_time: string;
  end_time?: string;
  session_name?: string;
  market_conditions?: string;
  session_notes?: string;
  total_trades: string;
  dominant_mood?: string;
  rule_breaks?: string[];
  created_at: string;
  updated_at: string;
}

export interface SessionReplayCreate {
  start_time: string;
  end_time?: string;
  session_name?: string;
  market_conditions?: string;
  session_notes?: string;
}

export interface SessionTimeline {
  session: SessionReplay;
  timeline: TimelineEvent[];
}

export interface TimelineEvent {
  type: 'mental_entry' | 'trade';
  timestamp: string;
  data: any;
}

export interface MoodPattern {
  mood_distribution: Record<string, number>;
  mood_trend: Array<{
    date: string;
    dominant_mood: string;
    mood_count: number;
  }>;
  insights: string[];
}

export interface RuleBreakAnalysis {
  rule_break_distribution: Record<string, number>;
  rule_break_trend: Array<{
    date: string;
    rule_breaks: number;
    unique_breaks: number;
  }>;
  insights: string[];
}

export const mentalMapService = {
  // Mental Map Entries
  async createMentalEntry(data: MentalMapEntryCreate): Promise<MentalMapEntry> {
    const response = await api.post('/mental-map/entries', data);
    return response.data;
  },

  async getMentalEntries(params?: {
    session_id?: string;
    trade_id?: string;
    start_date?: string;
    end_date?: string;
    mood?: string;
    limit?: number;
  }): Promise<MentalMapEntry[]> {
    const response = await api.get('/mental-map/entries', { params });
    return response.data;
  },

  async getMentalEntry(entryId: string): Promise<MentalMapEntry> {
    const response = await api.get(`/mental-map/entries/${entryId}`);
    return response.data;
  },

  async updateMentalEntry(entryId: string, data: Partial<MentalMapEntryCreate>): Promise<MentalMapEntry> {
    const response = await api.put(`/mental-map/entries/${entryId}`, data);
    return response.data;
  },

  async deleteMentalEntry(entryId: string): Promise<void> {
    await api.delete(`/mental-map/entries/${entryId}`);
  },

  // Session Replays
  async createSession(data: SessionReplayCreate): Promise<SessionReplay> {
    const response = await api.post('/mental-map/sessions', data);
    return response.data;
  },

  async getSessions(params?: {
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<SessionReplay[]> {
    const response = await api.get('/mental-map/sessions', { params });
    return response.data;
  },

  async getSession(sessionId: string): Promise<SessionReplay> {
    const response = await api.get(`/mental-map/sessions/${sessionId}`);
    return response.data;
  },

  async updateSession(sessionId: string, data: Partial<SessionReplayCreate>): Promise<SessionReplay> {
    const response = await api.put(`/mental-map/sessions/${sessionId}`, data);
    return response.data;
  },

  async getSessionTimeline(sessionId: string): Promise<SessionTimeline> {
    const response = await api.get(`/mental-map/sessions/${sessionId}/timeline`);
    return response.data;
  },

  // Analytics
  async getMoodPatterns(days: number = 30): Promise<MoodPattern> {
    const response = await api.get('/mental-map/analytics/mood-patterns', { params: { days } });
    return response.data;
  },

  async getRuleBreakAnalysis(days: number = 30): Promise<RuleBreakAnalysis> {
    const response = await api.get('/mental-map/analytics/rule-breaks', { params: { days } });
    return response.data;
  }
};
