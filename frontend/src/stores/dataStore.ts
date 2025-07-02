
import { create } from 'zustand';
import { api } from '../lib/api';

interface Trade {
  id: string;
  symbol: string;
  entry_time: string;
  exit_time: string;
  direction: 'long' | 'short';
  quantity: number;
  entry_price: number;
  exit_price: number;
  pnl: number;
}

interface Analytics {
  total_trades: number;
  total_pnl: number;
  win_rate: number;
  profit_factor: number;
  max_drawdown: number;
  sharpe_ratio: number;
  best_day: number;
  worst_day: number;
  avg_daily_pnl: number;
  risk_reward_ratio: number;
  equity_curve: Array<{ date: string; cumulativePnL: number }>;
  pnl_distribution: Array<{ range: string; count: number }>;
  symbol_breakdown: Array<{
    name: string;
    trades: number;
    winRate: number;
    pnl: number;
  }>;
}

interface DataState {
  tradeData: Trade[] | null;
  analytics: Analytics | null;
  isLoading: boolean;
  error: string | null;
  uploadProgress: number;
  
  // Actions
  setTradeData: (data: Trade[]) => void;
  setAnalytics: (analytics: Analytics) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  uploadData: (formData: FormData, onProgress?: (progress: number) => void) => Promise<any>;
  analyzeData: (data: any) => Promise<void>;
  clearData: () => void;
}

export const useDataStore = create<DataState>((set, get) => ({
  tradeData: null,
  analytics: null,
  isLoading: false,
  error: null,
  uploadProgress: 0,

  setTradeData: (data) => set({ tradeData: data }),
  setAnalytics: (analytics) => set({ analytics }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),

  uploadData: async (formData, onProgress) => {
    set({ isLoading: true, error: null, uploadProgress: 0 });

    try {
      const response = await api.post('/data/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 1)
          );
          set({ uploadProgress: progress });
          onProgress?.(progress);
        },
      });

      set({ 
        isLoading: false, 
        uploadProgress: 100,
        tradeData: response.data.data || []
      });

      return response.data;
    } catch (error: any) {
      set({ 
        isLoading: false, 
        error: error.response?.data?.detail || 'Upload failed',
        uploadProgress: 0
      });
      throw error;
    }
  },

  analyzeData: async (data) => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.post('/analytics/analyze', {
        data: data || get().tradeData,
        analysis_type: 'comprehensive'
      });

      const results = response.data.results;
      
      // Transform backend results to frontend analytics format
      const analytics: Analytics = {
        total_trades: results.total_trades || 0,
        total_pnl: results.total_pnl || 0,
        win_rate: results.win_rate || 0,
        profit_factor: results.profit_factor || 0,
        max_drawdown: results.max_drawdown || 0,
        sharpe_ratio: results.sharpe_ratio || 0,
        best_day: results.best_trade || 0,
        worst_day: results.worst_trade || 0,
        avg_daily_pnl: results.expectancy || 0,
        risk_reward_ratio: results.reward_risk || 0,
        equity_curve: results.equity_curve?.map((value: number, index: number) => ({
          date: `Trade ${index + 1}`,
          cumulativePnL: value
        })) || [],
        pnl_distribution: generatePnLDistribution(get().tradeData || []),
        symbol_breakdown: generateSymbolBreakdown(get().tradeData || [])
      };

      set({ analytics, isLoading: false });
    } catch (error: any) {
      set({ 
        isLoading: false, 
        error: error.response?.data?.detail || 'Analysis failed'
      });
      throw error;
    }
  },

  clearData: () => set({ 
    tradeData: null, 
    analytics: null, 
    error: null, 
    uploadProgress: 0 
  }),
}));

// Helper functions
function generatePnLDistribution(trades: Trade[]): Array<{ range: string; count: number }> {
  const ranges = [
    { min: -Infinity, max: -1000, label: '< -$1000' },
    { min: -1000, max: -500, label: '-$1000 to -$500' },
    { min: -500, max: -100, label: '-$500 to -$100' },
    { min: -100, max: 0, label: '-$100 to $0' },
    { min: 0, max: 100, label: '$0 to $100' },
    { min: 100, max: 500, label: '$100 to $500' },
    { min: 500, max: 1000, label: '$500 to $1000' },
    { min: 1000, max: Infinity, label: '> $1000' },
  ];

  return ranges.map(range => ({
    range: range.label,
    count: trades.filter(trade => 
      trade.pnl > range.min && trade.pnl <= range.max
    ).length
  }));
}

function generateSymbolBreakdown(trades: Trade[]): Array<{
  name: string;
  trades: number;
  winRate: number;
  pnl: number;
}> {
  const symbolMap = new Map();

  trades.forEach(trade => {
    if (!symbolMap.has(trade.symbol)) {
      symbolMap.set(trade.symbol, {
        name: trade.symbol,
        trades: 0,
        wins: 0,
        pnl: 0
      });
    }

    const symbolData = symbolMap.get(trade.symbol);
    symbolData.trades++;
    if (trade.pnl > 0) symbolData.wins++;
    symbolData.pnl += trade.pnl;
  });

  return Array.from(symbolMap.values()).map(symbol => ({
    name: symbol.name,
    trades: symbol.trades,
    winRate: Math.round((symbol.wins / symbol.trades) * 100),
    pnl: symbol.pnl
  }));
}
