
import { create } from 'zustand';
import { tradesService, TradeCreateRequest, TradeQueryParams } from '../services/trades';
import { Trade, Analytics } from '../types';

interface TradesState {
  trades: Trade[];
  currentTrade: Trade | null;
  analytics: Analytics | null;
  isLoading: boolean;
  error: string | null;
  pagination: {
    total: number;
    page: number;
    per_page: number;
    pages: number;
  };
  filters: TradeQueryParams;

  // Actions
  fetchTrades: (params?: TradeQueryParams) => Promise<void>;
  createTrade: (tradeData: TradeCreateRequest) => Promise<void>;
  updateTrade: (tradeId: string, updateData: any) => Promise<void>;
  deleteTrade: (tradeId: string) => Promise<void>;
  fetchAnalytics: (startDate?: string, endDate?: string) => Promise<void>;
  setFilters: (filters: TradeQueryParams) => void;
  clearError: () => void;
  setCurrentTrade: (trade: Trade | null) => void;
}

export const useTradeStore = create<TradesState>((set, get) => ({
  trades: [],
  currentTrade: null,
  analytics: null,
  isLoading: false,
  error: null,
  pagination: {
    total: 0,
    page: 1,
    per_page: 50,
    pages: 0
  },
  filters: {},

  fetchTrades: async (params?: TradeQueryParams) => {
    set({ isLoading: true, error: null });
    try {
      const queryParams = { ...get().filters, ...params };
      const response = await tradesService.getTrades(queryParams);
      
      set({
        trades: response.data.items,
        pagination: {
          total: response.data.total,
          page: response.data.page,
          per_page: response.data.per_page,
          pages: response.data.pages
        },
        isLoading: false
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch trades',
        isLoading: false
      });
    }
  },

  createTrade: async (tradeData: TradeCreateRequest) => {
    set({ isLoading: true, error: null });
    try {
      const newTrade = await tradesService.createTrade(tradeData);
      set(state => ({
        trades: [newTrade, ...state.trades],
        isLoading: false
      }));
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to create trade',
        isLoading: false
      });
      throw error;
    }
  },

  updateTrade: async (tradeId: string, updateData: any) => {
    set({ isLoading: true, error: null });
    try {
      const updatedTrade = await tradesService.updateTrade(tradeId, updateData);
      set(state => ({
        trades: state.trades.map(trade => 
          trade.id === tradeId ? updatedTrade : trade
        ),
        currentTrade: state.currentTrade?.id === tradeId ? updatedTrade : state.currentTrade,
        isLoading: false
      }));
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to update trade',
        isLoading: false
      });
      throw error;
    }
  },

  deleteTrade: async (tradeId: string) => {
    set({ isLoading: true, error: null });
    try {
      await tradesService.deleteTrade(tradeId);
      set(state => ({
        trades: state.trades.filter(trade => trade.id !== tradeId),
        currentTrade: state.currentTrade?.id === tradeId ? null : state.currentTrade,
        isLoading: false
      }));
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to delete trade',
        isLoading: false
      });
      throw error;
    }
  },

  fetchAnalytics: async (startDate?: string, endDate?: string) => {
    set({ isLoading: true, error: null });
    try {
      const analytics = await tradesService.getDashboardAnalytics(startDate, endDate);
      set({ analytics, isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch analytics',
        isLoading: false
      });
    }
  },

  setFilters: (filters: TradeQueryParams) => {
    set({ filters });
    get().fetchTrades(filters);
  },

  clearError: () => set({ error: null }),

  setCurrentTrade: (trade: Trade | null) => set({ currentTrade: trade })
}));
