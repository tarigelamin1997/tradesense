
import { apiClient } from './api';

export interface FeatureRequest {
  id: string;
  title: string;
  description: string;
  category: string;
  status: string;
  priority: string;
  upvotes: number;
  downvotes: number;
  net_votes: number;
  user_vote?: 'upvote' | 'downvote';
  created_at: string;
  updated_at: string;
  user_id: string;
}

export interface CreateFeatureRequest {
  title: string;
  description: string;
  category: string;
}

export interface FeatureComment {
  id: string;
  content: string;
  user_id: string;
  created_at: string;
}

export interface FeatureStats {
  total_requests: number;
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  top_voted: FeatureRequest[];
  recent_requests: FeatureRequest[];
}

interface GetFeaturesParams {
  category?: string;
  status?: string;
  sort_by?: string;
  limit?: number;
  offset?: number;
}

class FeatureService {
  async getFeatures(params: GetFeaturesParams = {}): Promise<FeatureRequest[]> {
    const searchParams = new URLSearchParams();
    
    if (params.category) searchParams.append('category', params.category);
    if (params.status) searchParams.append('status', params.status);
    if (params.sort_by) searchParams.append('sort_by', params.sort_by);
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.offset) searchParams.append('offset', params.offset.toString());
    
    const response = await apiClient.get(`/features?${searchParams.toString()}`);
    return response.data;
  }

  async getFeature(featureId: string): Promise<FeatureRequest> {
    const response = await apiClient.get(`/features/${featureId}`);
    return response.data;
  }

  async createFeature(feature: CreateFeatureRequest): Promise<FeatureRequest> {
    const response = await apiClient.post('/features', feature);
    return response.data;
  }

  async voteOnFeature(featureId: string, voteType: 'upvote' | 'downvote'): Promise<any> {
    const response = await apiClient.post(`/features/${featureId}/vote`, {
      vote_type: voteType
    });
    return response.data;
  }

  async addComment(featureId: string, content: string): Promise<FeatureComment> {
    const response = await apiClient.post(`/features/${featureId}/comments`, {
      content
    });
    return response.data;
  }

  async getComments(featureId: string): Promise<FeatureComment[]> {
    const response = await apiClient.get(`/features/${featureId}/comments`);
    return response.data;
  }

  async updateFeature(featureId: string, updates: Partial<FeatureRequest>): Promise<FeatureRequest> {
    const response = await apiClient.put(`/features/${featureId}`, updates);
    return response.data;
  }

  async deleteFeature(featureId: string): Promise<void> {
    await apiClient.delete(`/features/${featureId}`);
  }

  async getStats(): Promise<FeatureStats> {
    const response = await apiClient.get('/features/stats/summary');
    return response.data;
  }
}

export const featureService = new FeatureService();
