
import { api } from './api';

export interface DailyTimelineData {
  date: string;
  pnl: number;
  trade_count: number;
  dominant_emotion?: string;
  emotion_emoji?: string;
  trades: Array<{
    id: string;
    symbol: string;
    pnl: number;
    strategy?: string;
    entry_time: string;
  }>;
  mood_score?: number;
  reflection_summary?: string;
}

export interface TimelineResponse {
  timeline_data: Record<string, DailyTimelineData>;
  date_range: {
    start_date: string;
    end_date: string;
  };
  total_days: number;
  trading_days: number;
  best_day?: DailyTimelineData;
  worst_day?: DailyTimelineData;
  emotional_patterns: {
    most_common_emotion?: string;
    emotion_frequency: Record<string, number>;
    emotion_profitability: Record<string, number>;
    best_weekday?: string;
    worst_weekday?: string;
    weekday_performance: Record<string, number>;
  };
}

export interface DailyReflection {
  id?: string;
  reflection_date: string;
  mood_score?: number;
  summary?: string;
  dominant_emotion?: string;
}

class TimelineService {
  async getTimeline(startDate?: string, endDate?: string): Promise<TimelineResponse> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await api.get(`/analytics/timeline?${params.toString()}`);
    return response.data;
  }

  async getDailyReflection(date: string): Promise<DailyReflection | null> {
    try {
      const response = await api.get(`/reflections/${date}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  }

  async saveDailyReflection(reflection: DailyReflection): Promise<DailyReflection> {
    if (reflection.id) {
      const response = await api.put(`/reflections/${reflection.reflection_date}`, reflection);
      return response.data;
    } else {
      const response = await api.post('/reflections/', reflection);
      return response.data;
    }
  }

  async deleteDailyReflection(date: string): Promise<void> {
    await api.delete(`/reflections/${date}`);
  }
}

export const timelineService = new TimelineService();
