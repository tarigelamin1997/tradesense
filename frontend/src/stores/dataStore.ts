
import { create } from 'zustand';
import { Trade, DashboardMetrics } from '@/types';

interface DataState {
  trades: Trade[];
  dashboardMetrics: DashboardMetrics | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setTrades: (trades: Trade[]) => void;
  setDashboardMetrics: (metrics: DashboardMetrics) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearData: () => void;
}

export const useDataStore = create<DataState>((set) => ({
  trades: [],
  dashboardMetrics: null,
  isLoading: false,
  error: null,
  
  setTrades: (trades) => set({ trades }),
  setDashboardMetrics: (dashboardMetrics) => set({ dashboardMetrics }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  clearData: () => set({ trades: [], dashboardMetrics: null, error: null }),
}));
