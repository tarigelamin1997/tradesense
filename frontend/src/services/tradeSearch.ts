
import { api } from './api';

export interface SearchFilters {
  query?: string;
  tags?: string[];
  instruments?: string[];
  strategies?: string[];
  winOnly?: boolean;
  lossOnly?: boolean;
  startDate?: string;
  endDate?: string;
  minPnl?: number;
  maxPnl?: number;
  limit?: number;
  offset?: number;
}

export interface SearchResult {
  trades: Trade[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
  filters: {
    availableTags: string[];
    availableInstruments: string[];
    availableStrategies: string[];
  };
  appliedFilters: SearchFilters;
}

export interface Trade {
  id: string;
  symbol: string;
  direction: 'long' | 'short';
  quantity: number;
  entryPrice: number;
  exitPrice?: number;
  entryTime: string;
  exitTime?: string;
  pnl?: number;
  netPnl?: number;
  notes?: string;
  tags: string[];
  strategyTag?: string;
  confidenceScore?: number;
  createdAt: string;
  updatedAt: string;
}

export interface FilterOptions {
  tags: string[];
  instruments: string[];
  strategies: string[];
}

export const tradeSearchService = {
  async searchTrades(filters: SearchFilters): Promise<SearchResult> {
    const params = new URLSearchParams();
    
    if (filters.query) params.append('query', filters.query);
    if (filters.tags?.length) {
      filters.tags.forEach(tag => params.append('tags', tag));
    }
    if (filters.instruments?.length) {
      filters.instruments.forEach(instrument => params.append('instruments', instrument));
    }
    if (filters.strategies?.length) {
      filters.strategies.forEach(strategy => params.append('strategies', strategy));
    }
    if (filters.winOnly !== undefined) params.append('win_only', filters.winOnly.toString());
    if (filters.lossOnly !== undefined) params.append('loss_only', filters.lossOnly.toString());
    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);
    if (filters.minPnl !== undefined) params.append('min_pnl', filters.minPnl.toString());
    if (filters.maxPnl !== undefined) params.append('max_pnl', filters.maxPnl.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.offset) params.append('offset', filters.offset.toString());

    const response = await api.get(`/trades/search?${params.toString()}`);
    return {
      trades: response.data.data.trades.map(this.transformTrade),
      pagination: response.data.data.pagination,
      filters: response.data.data.filters,
      appliedFilters: response.data.data.applied_filters
    };
  },

  async getFilterOptions(): Promise<FilterOptions> {
    const response = await api.get('/trades/filters/options');
    return response.data.data;
  },

  transformTrade(trade: any): Trade {
    return {
      id: trade.id,
      symbol: trade.symbol,
      direction: trade.direction,
      quantity: trade.quantity,
      entryPrice: trade.entry_price,
      exitPrice: trade.exit_price,
      entryTime: trade.entry_time,
      exitTime: trade.exit_time,
      pnl: trade.pnl,
      netPnl: trade.net_pnl,
      notes: trade.notes,
      tags: trade.tags || [],
      strategyTag: trade.strategy_tag,
      confidenceScore: trade.confidence_score,
      createdAt: trade.created_at,
      updatedAt: trade.updated_at
    };
  }
};
