
import { create } from 'zustand';
import { tradesService, type Trade, type Analytics, type UploadResponse } from '../services/trades';

interface TradeState {
  trades: Trade[];
  analytics: Analytics | null;
  isLoading: boolean;
  error: string | null;
}

interface TradeActions {
  uploadData: (formData: FormData, onProgress?: (progress: number) => void) => Promise<UploadResponse>;
  analyzeData: (trades: Trade[]) => Promise<void>;
  fetchTrades: () => Promise<void>;
  fetchAnalytics: () => Promise<void>;
  clearError: () => void;
  setAnalytics: (analytics: Analytics) => void;
}

export const useTradeStore = create<TradeState & TradeActions>((set, get) => ({
  trades: [],
  analytics: null,
  isLoading: false,
  error: null,

  uploadData: async (formData: FormData, onProgress?: (progress: number) => void) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await tradesService.uploadTrades(formData, onProgress);
      
      if (response.success && response.data) {
        set({
          trades: response.data,
          isLoading: false,
          error: null,
        });
      }
      
      return response;
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.response?.data?.detail || 'Upload failed',
      });
      throw error;
    }
  },

  analyzeData: async (trades: Trade[]) => {
    set({ isLoading: true, error: null });
    
    try {
      const analytics = await tradesService.analyzeTrades(trades);
      
      set({
        analytics,
        isLoading: false,
        error: null,
      });
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.response?.data?.detail || 'Analysis failed',
      });
      throw error;
    }
  },

  fetchTrades: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const trades = await tradesService.getTrades();
      
      set({
        trades,
        isLoading: false,
        error: null,
      });
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.response?.data?.detail || 'Failed to fetch trades',
      });
    }
  },

  fetchAnalytics: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const analytics = await tradesService.getAnalytics();
      
      set({
        analytics,
        isLoading: false,
        error: null,
      });
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.response?.data?.detail || 'Failed to fetch analytics',
      });
    }
  },

  clearError: () => {
    set({ error: null });
  },

  setAnalytics: (analytics: Analytics) => {
    set({ analytics });
  },
}));
