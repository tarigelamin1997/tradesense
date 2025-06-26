
import { api } from './api';

export interface CritiqueData {
  summary: string;
  suggestion: string;
  confidence: number;
  tags: string[];
  technical_analysis: string;
  psychological_analysis: string;
  risk_assessment: string;
  generated_at: string;
  version: string;
}

export interface CritiqueFeedback {
  helpful: boolean;
  feedback_text?: string;
  rating?: number;
}

export interface CritiqueAnalytics {
  total_critiques: number;
  average_confidence: number;
  most_common_tags: Array<{ tag: string; count: number }>;
  feedback_stats: {
    total_feedback: number;
    helpful_percentage: number;
  };
}

export const critiqueService = {
  async getTradeCritique(tradeId: string, regenerate: boolean = false): Promise<CritiqueData> {
    const response = await api.get(`/critique/trades/${tradeId}?regenerate=${regenerate}`);
    return response.data;
  },

  async submitFeedback(tradeId: string, feedback: CritiqueFeedback): Promise<{ message: string }> {
    const response = await api.post(`/critique/trades/${tradeId}/feedback`, feedback);
    return response.data;
  },

  async regenerateCritique(tradeId: string): Promise<CritiqueData> {
    const response = await api.post(`/critique/trades/${tradeId}/regenerate`);
    return response.data;
  },

  async getCritiqueAnalytics(): Promise<CritiqueAnalytics> {
    const response = await api.get('/critique/analytics');
    return response.data;
  }
};
