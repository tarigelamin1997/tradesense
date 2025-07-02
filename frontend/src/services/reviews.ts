
import { api } from './api';

export interface TradeReview {
  id: string;
  trade_id: string;
  quality_score: number;
  mistakes: string[];
  mood?: string;
  lesson_learned?: string;
  execution_vs_plan?: number;
  created_at: string;
  updated_at: string;
}

export interface TradeReviewCreate {
  quality_score: number;
  mistakes: string[];
  mood?: string;
  lesson_learned?: string;
  execution_vs_plan?: number;
}

export interface ReviewPatterns {
  total_reviews: number;
  avg_quality_score: number;
  most_common_mistakes: Array<{
    mistake: string;
    count: number;
    percentage: number;
  }>;
  mood_performance: Array<{
    mood: string;
    avg_quality: number;
    count: number;
  }>;
  quality_trend: Array<{
    date: string;
    avg_quality: number;
  }>;
  improvement_areas: string[];
  strengths: string[];
}

export interface ReviewInsights {
  patterns: ReviewPatterns;
  recommendations: string[];
  warnings: string[];
  achievements: string[];
}

export const reviewsService = {
  // Create a review for a trade
  createReview: async (tradeId: string, reviewData: TradeReviewCreate): Promise<TradeReview> => {
    const response = await api.post(`/reviews/trades/${tradeId}`, reviewData);
    return response.data;
  },

  // Update an existing review
  updateReview: async (tradeId: string, reviewData: Partial<TradeReviewCreate>): Promise<TradeReview> => {
    const response = await api.put(`/reviews/trades/${tradeId}`, reviewData);
    return response.data;
  },

  // Get review for a specific trade
  getTradeReview: async (tradeId: string): Promise<TradeReview | null> => {
    try {
      const response = await api.get(`/reviews/trades/${tradeId}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  // Delete a review
  deleteReview: async (tradeId: string): Promise<void> => {
    await api.delete(`/reviews/trades/${tradeId}`);
  },

  // Get all user reviews
  getUserReviews: async (limit = 50, offset = 0): Promise<TradeReview[]> => {
    const response = await api.get('/reviews/', {
      params: { limit, offset }
    });
    return response.data;
  },

  // Get review patterns analysis
  getReviewPatterns: async (days = 30): Promise<ReviewPatterns> => {
    const response = await api.get('/reviews/analytics/patterns', {
      params: { days }
    });
    return response.data;
  },

  // Get actionable insights
  getReviewInsights: async (days = 30): Promise<ReviewInsights> => {
    const response = await api.get('/reviews/analytics/insights', {
      params: { days }
    });
    return response.data;
  },
};

// Predefined mistake and mood options
export const MISTAKE_OPTIONS = [
  'early_entry', 'late_entry', 'no_confirmation', 'wrong_size',
  'missed_stop', 'early_exit', 'late_exit', 'revenge_trade',
  'overtrading', 'fomo', 'hesitation', 'greed', 'fear',
  'poor_timing', 'ignored_plan', 'emotional_decision'
];

export const MOOD_OPTIONS = [
  'calm', 'confident', 'focused', 'anxious', 'impulsive',
  'frustrated', 'greedy', 'fearful', 'rushed', 'patient'
];

// Helper function to format mistake tags
export const formatMistakeTag = (tag: string): string => {
  return tag.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');
};

export const formatMoodTag = (tag: string): string => {
  return tag.charAt(0).toUpperCase() + tag.slice(1);
};
