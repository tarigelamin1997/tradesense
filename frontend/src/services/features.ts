import { api } from './api';

export interface FeatureRequest {
  id: string;
  title: string;
  description: string;
  category: string;
  status: string;
  priority: string;
  upvotes: number;
  downvotes: number;
  created_at: string;
  updated_at: string;
  user_id: string;
}

export interface FeatureRequestCreate {
  title: string;
  description: string;
  category: string;
  priority?: string;
}

export interface FeatureVoteCreate {
  feature_request_id: string;
  vote_type: 'upvote' | 'downvote';
}

export interface FeatureCommentCreate {
  feature_request_id: string;
  content: string;
}

export interface GetFeaturesParams {
  category?: string;
  status?: string;
  sort_by?: string;
  skip?: number;
  limit?: number;
}

export const featuresService = {
  async getFeatures(params: GetFeaturesParams = {}) {
    const queryParams = new URLSearchParams();

    if (params.category && params.category !== 'all') {
      queryParams.append('category', params.category);
    }
    if (params.status && params.status !== 'all') {
      queryParams.append('status', params.status);
    }
    if (params.sort_by) {
      queryParams.append('sort_by', params.sort_by);
    }
    if (params.skip) {
      queryParams.append('skip', params.skip.toString());
    }
    if (params.limit) {
      queryParams.append('limit', params.limit.toString());
    }

    const response = await api.get(`/features?${queryParams.toString()}`);
    return response.data;
  },

  async getFeatureById(id: string) {
    const response = await api.get(`/features/${id}`);
    return response.data;
  },

  async createFeature(feature: FeatureRequestCreate) {
    const response = await api.post('/features', feature);
    return response.data;
  },

  async updateFeature(id: string, updates: Partial<FeatureRequest>) {
    const response = await api.put(`/features/${id}`, updates);
    return response.data;
  },

  async voteOnFeature(vote: FeatureVoteCreate) {
    const response = await api.post('/features/vote', vote);
    return response.data;
  },

  async addComment(comment: FeatureCommentCreate) {
    const response = await api.post('/features/comments', comment);
    return response.data;
  },

  async getFeatureComments(featureId: string) {
    const response = await api.get(`/features/${featureId}/comments`);
    return response.data;
  }
};