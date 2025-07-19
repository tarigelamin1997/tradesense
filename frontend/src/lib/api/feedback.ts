import { api } from './client';

export interface FeedbackData {
  type: 'bug' | 'feature' | 'performance' | 'ux' | 'other';
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  expectedBehavior?: string;
  actualBehavior?: string;
  email?: string;
  url: string;
  userAgent: string;
  screenResolution: string;
  previousPages: string[];
  lastActions: any[];
  errorLogs: any[];
  screenshot?: string;
  timestamp: string;
}

export interface FeedbackResponse {
  trackingId: string;
  message: string;
}

export interface FeedbackPattern {
  id: string;
  pattern_signature: string;
  pattern_type: string;
  occurrences: number;
  affected_users: number;
  first_seen: string;
  last_seen: string;
  root_cause?: string;
  resolution?: string;
}

export interface FeedbackAnalytics {
  top_issues: Array<{
    pattern_id: string;
    title: string;
    count: number;
    severity: string;
  }>;
  trending_issues: Array<{
    pattern_id: string;
    title: string;
    growth_rate: number;
  }>;
  critical_patterns: FeedbackPattern[];
  resolution_time: {
    average_hours: number;
    by_severity: Record<string, number>;
  };
  user_impact: {
    total_affected: number;
    by_tier: Record<string, number>;
  };
  churn_correlation: {
    high_risk_patterns: string[];
    estimated_revenue_impact: number;
  };
}

export interface FeedbackItem {
  id: string;
  user_id?: string;
  type: string;
  severity: string;
  title: string;
  description: string;
  status: 'new' | 'investigating' | 'in_progress' | 'resolved' | 'closed';
  url: string;
  user_agent: string;
  screen_resolution: string;
  subscription_tier?: string;
  created_at: string;
  resolved_at?: string;
  resolution_notes?: string;
  assigned_to?: string;
  duplicate_count: number;
  affected_users: number;
}

export interface FeedbackHeatmapData {
  page: string;
  issue_count: number;
  severity_breakdown: Record<string, number>;
}

export interface ImpactAnalysis {
  affected_features: string[];
  user_segments: Record<string, number>;
  revenue_at_risk: number;
  churn_probability: number;
}

export const feedbackApi = {
  // Submit new feedback
  async submit(data: FeedbackData): Promise<FeedbackResponse> {
    const response = await api.post<FeedbackResponse>('/api/v1/feedback/submit', data);
    return response.data;
  },

  // Get feedback analytics (admin)
  async getAnalytics(): Promise<FeedbackAnalytics> {
    const response = await api.get<FeedbackAnalytics>('/api/v1/feedback/analytics');
    return response.data;
  },

  // Get pattern details (admin)
  async getPatternDetails(patternId: string): Promise<{
    pattern: FeedbackPattern;
    related_feedback: FeedbackItem[];
    suggested_fixes: string[];
  }> {
    const response = await api.get(`/api/v1/feedback/patterns/${patternId}`);
    return response.data;
  },

  // Get all feedback (admin)
  async list(filters?: {
    status?: string;
    type?: string;
    severity?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<FeedbackItem[]> {
    const response = await api.get<FeedbackItem[]>('/api/v1/feedback/list', {
      params: filters
    });
    return response.data;
  },

  // Update feedback status (admin)
  async updateStatus(
    feedbackId: string, 
    status: string, 
    notes?: string
  ): Promise<FeedbackItem> {
    const response = await api.patch<FeedbackItem>(
      `/api/v1/feedback/${feedbackId}/status`,
      { status, resolution_notes: notes }
    );
    return response.data;
  },

  // Assign feedback (admin)
  async assign(feedbackId: string, assignee: string): Promise<FeedbackItem> {
    const response = await api.patch<FeedbackItem>(
      `/api/v1/feedback/${feedbackId}/assign`,
      { assigned_to: assignee }
    );
    return response.data;
  },

  // Mark as duplicate (admin)
  async markDuplicate(feedbackId: string, originalId: string): Promise<void> {
    await api.post(`/api/v1/feedback/${feedbackId}/duplicate`, {
      original_id: originalId
    });
  },

  // Get user's feedback history
  async getUserFeedback(): Promise<FeedbackItem[]> {
    const response = await api.get<FeedbackItem[]>('/api/v1/feedback/my-feedback');
    return response.data;
  },

  // Get dashboard data (admin)
  async getDashboard(): Promise<{
    recent_feedback: FeedbackItem[];
    critical_issues: FeedbackItem[];
    trending_patterns: any[];
    resolution_stats: any;
    impact_analysis: any;
    feedback_heatmap: FeedbackHeatmapData[];
  }> {
    const response = await api.get('/api/v1/feedback/dashboard');
    return response.data;
  },

  // Train pattern detection (admin)
  async trainPatternDetection(): Promise<{
    message: string;
    patterns_discovered: number;
    accuracy: number;
  }> {
    const response = await api.post('/api/v1/feedback/patterns/train');
    return response.data;
  }
};