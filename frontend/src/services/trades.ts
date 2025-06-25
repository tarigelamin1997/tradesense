
import { apiClient } from './api';
import { Trade, Analytics } from '../types';

export interface TradeCreateRequest {
  symbol: string;
  direction: 'long' | 'short';
  quantity: number;
  entry_price: number;
  entry_time: string;
  strategy_tag?: string;
  confidence_score?: number;
  notes?: string;
}

export interface TradeUpdateRequest {
  exit_price?: number;
  exit_time?: string;
  notes?: string;
  tags?: string[];
}

export interface TradeQueryParams {
  symbol?: string;
  strategy_tag?: string;
  start_date?: string;
  end_date?: string;
  status?: string;
  page?: number;
  per_page?: number;
}

export interface PaginatedTradesResponse {
  success: boolean;
  data: {
    items: Trade[];
    total: number;
    page: number;
    per_page: number;
    pages: number;
  };
  message: string;
}

export interface AnalyticsRequest {
  data: any[];
  analysis_type?: string;
}

class TradesService {
  async createTrade(tradeData: TradeCreateRequest): Promise<Trade> {
    const response = await apiClient.post<Trade>('/api/v1/trades/', tradeData);
    return response.data;
  }

  async getTrades(params: TradeQueryParams = {}): Promise<PaginatedTradesResponse> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, value.toString());
      }
    });

    const response = await apiClient.get<PaginatedTradesResponse>(
      `/api/v1/trades/?${queryParams.toString()}`
    );
    return response.data;
  }

  async getTrade(tradeId: string): Promise<Trade> {
    const response = await apiClient.get<Trade>(`/api/v1/trades/${tradeId}`);
    return response.data;
  }

  async updateTrade(tradeId: string, updateData: TradeUpdateRequest): Promise<Trade> {
    const response = await apiClient.put<Trade>(`/api/v1/trades/${tradeId}`, updateData);
    return response.data;
  }

  async deleteTrade(tradeId: string): Promise<void> {
    await apiClient.delete(`/api/v1/trades/${tradeId}`);
  }

  async calculateAnalytics(request: AnalyticsRequest): Promise<Analytics> {
    const response = await apiClient.post<Analytics>('/api/v1/trades/analytics', request);
    return response.data;
  }

  async getDashboardAnalytics(startDate?: string, endDate?: string): Promise<Analytics> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await apiClient.get<{ data: Analytics; success: boolean }>(
      `/api/v1/trades/analytics/dashboard?${params.toString()}`
    );
    return response.data.data;
  }
}

export const tradesService = new TradesService();
