
import { api } from './api';

export interface Milestone {
  id: string;
  user_id: string;
  type: string;
  category: string;
  title: string;
  description: string;
  achieved_at: string;
  value?: number;
  target_value?: number;
  xp_points: number;
  badge_icon?: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  metadata?: Record<string, any>;
  created_at: string;
}

export interface UserProgress {
  total_xp: number;
  total_milestones: number;
  level: number;
  level_progress: number;
  xp_to_next_level: number;
  recent_milestones: Milestone[];
  category_progress: Record<string, {
    count: number;
    xp: number;
    recent: string | null;
  }>;
  active_streaks: {
    journaling_days: number;
    win_streak: number;
    discipline_streak: number;
  };
}

export interface LeaderboardEntry {
  user_id: string;
  username: string;
  total_xp: number;
  level: number;
  total_milestones: number;
  rank: number;
}

export interface MilestoneCheckResult {
  message: string;
  awarded_count: number;
  new_milestones: {
    title: string;
    description: string;
    xp_points: number;
    badge_icon: string;
    rarity: string;
  }[];
}

class MilestoneService {
  async getMilestones(params?: {
    limit?: number;
    category?: string;
  }): Promise<Milestone[]> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.category) searchParams.append('category', params.category);
    
    const response = await api.get(`/milestones?${searchParams}`);
    return response.data;
  }

  async getUserProgress(): Promise<UserProgress> {
    const response = await api.get('/milestones/progress');
    return response.data;
  }

  async triggerMilestoneCheck(
    triggerType: string,
    context: Record<string, any> = {}
  ): Promise<MilestoneCheckResult> {
    const response = await api.post(`/milestones/check/${triggerType}`, context);
    return response.data;
  }

  async getLeaderboard(limit: number = 10): Promise<{
    leaderboard: LeaderboardEntry[];
    user_rank: number;
    total_users: number;
  }> {
    const response = await api.get(`/milestones/leaderboard?limit=${limit}`);
    return response.data;
  }

  // Helper methods for milestone checking
  async checkJournalingMilestones(): Promise<MilestoneCheckResult> {
    return this.triggerMilestoneCheck('trade_logged');
  }

  async checkPerformanceMilestones(): Promise<MilestoneCheckResult> {
    return this.triggerMilestoneCheck('trade_completed');
  }

  async checkAnalyticsMilestones(analyticsType: string, context: Record<string, any> = {}): Promise<MilestoneCheckResult> {
    return this.triggerMilestoneCheck('analytics_used', {
      analytics_type: analyticsType,
      ...context
    });
  }

  async checkDisciplineMilestones(): Promise<MilestoneCheckResult> {
    return this.triggerMilestoneCheck('discipline_check');
  }

  // Utility methods
  getRarityColor(rarity: string): string {
    switch (rarity) {
      case 'common': return '#9CA3AF'; // Gray
      case 'rare': return '#3B82F6'; // Blue
      case 'epic': return '#8B5CF6'; // Purple
      case 'legendary': return '#F59E0B'; // Gold
      default: return '#9CA3AF';
    }
  }

  getRarityGlow(rarity: string): string {
    switch (rarity) {
      case 'common': return '0 0 5px rgba(156, 163, 175, 0.3)';
      case 'rare': return '0 0 10px rgba(59, 130, 246, 0.5)';
      case 'epic': return '0 0 15px rgba(139, 92, 246, 0.7)';
      case 'legendary': return '0 0 20px rgba(245, 158, 11, 0.9)';
      default: return 'none';
    }
  }

  getLevelTitle(level: number): string {
    const titles = [
      'Rookie Trader', 'Learning Trader', 'Developing Trader', 'Skilled Trader',
      'Advanced Trader', 'Expert Trader', 'Master Trader', 'Elite Trader',
      'Legendary Trader', 'Mythical Trader', 'Grandmaster Trader'
    ];
    
    if (level < titles.length) {
      return titles[level];
    }
    
    return `Level ${level} Master`;
  }
}

export const milestoneService = new MilestoneService();
