
import { apiClient } from './api';

export interface Tag {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  color?: string;
  created_at: string;
  updated_at: string;
  trade_count?: number;
}

export interface TagCreate {
  name: string;
  description?: string;
  color?: string;
}

export interface TagUpdate {
  name?: string;
  description?: string;
  color?: string;
}

export interface PopularTag {
  name: string;
  usage_count: number;
  total_pnl: number;
  avg_pnl: number;
}

export interface TagAnalytics {
  tag: string;
  total_trades: number;
  total_pnl: number;
  avg_pnl: number;
  win_rate: number;
  winning_trades: number;
  losing_trades: number;
  best_trade: number;
  worst_trade: number;
}

class TagsService {
  async getTags(params: {
    page?: number;
    per_page?: number;
    search?: string;
  } = {}): Promise<{
    tags: Tag[];
    total_count: number;
    page: number;
    per_page: number;
    has_more: boolean;
  }> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, value.toString());
      }
    });

    const response = await apiClient.get(
      `/api/v1/tags/?${queryParams.toString()}`
    );
    return response.data;
  }

  async createTag(tagData: TagCreate): Promise<Tag> {
    const response = await apiClient.post<Tag>('/api/v1/tags/', tagData);
    return response.data;
  }

  async getTag(tagId: string): Promise<Tag> {
    const response = await apiClient.get<Tag>(`/api/v1/tags/${tagId}`);
    return response.data;
  }

  async updateTag(tagId: string, updateData: TagUpdate): Promise<Tag> {
    const response = await apiClient.put<Tag>(`/api/v1/tags/${tagId}`, updateData);
    return response.data;
  }

  async deleteTag(tagId: string): Promise<void> {
    await apiClient.delete(`/api/v1/tags/${tagId}`);
  }

  async getPopularTags(limit: number = 10): Promise<PopularTag[]> {
    const response = await apiClient.get<{ data: PopularTag[] }>(
      `/api/v1/tags/popular?limit=${limit}`
    );
    return response.data.data;
  }

  async assignTagsToTrade(tradeId: string, tagIds: string[]): Promise<void> {
    await apiClient.post(`/api/v1/tags/trades/${tradeId}/assign`, tagIds);
  }

  async removeTagsFromTrade(tradeId: string, tagIds: string[]): Promise<void> {
    await apiClient.delete(`/api/v1/tags/trades/${tradeId}/remove`, {
      data: tagIds
    });
  }

  async getTagAnalytics(tag: string): Promise<TagAnalytics> {
    const response = await apiClient.get<{ data: TagAnalytics }>(
      `/api/v1/trades/analytics/tags/${encodeURIComponent(tag)}`
    );
    return response.data.data;
  }
}

export const tagsService = new TagsService();
export default tagsService;
