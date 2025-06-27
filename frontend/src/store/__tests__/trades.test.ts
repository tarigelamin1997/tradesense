
import { renderHook, act } from '@testing-library/react';
import { useTradesStore } from '../trades';

const mockTrades = [
  {
    id: '1',
    symbol: 'AAPL',
    quantity: 100,
    price: 150.00,
    date: '2024-01-01',
    type: 'buy' as const,
    profit: 500.00
  },
  {
    id: '2',
    symbol: 'GOOGL',
    quantity: 50,
    price: 2800.00,
    date: '2024-01-02',
    type: 'sell' as const,
    profit: -200.00
  }
];

describe('Trades Store', () => {
  beforeEach(() => {
    useTradesStore.getState().clearTrades();
  });

  it('should initialize with empty state', () => {
    const { result } = renderHook(() => useTradesStore());
    
    expect(result.current.trades).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.analytics).toBeNull();
  });

  it('should set trades successfully', () => {
    const { result } = renderHook(() => useTradesStore());
    
    act(() => {
      result.current.setTrades(mockTrades);
    });

    expect(result.current.trades).toEqual(mockTrades);
    expect(result.current.trades).toHaveLength(2);
  });

  it('should add single trade', () => {
    const { result } = renderHook(() => useTradesStore());
    
    act(() => {
      result.current.addTrade(mockTrades[0]);
    });

    expect(result.current.trades).toHaveLength(1);
    expect(result.current.trades[0]).toEqual(mockTrades[0]);
  });

  it('should set loading state', () => {
    const { result } = renderHook(() => useTradesStore());
    
    act(() => {
      result.current.setLoading(true);
    });

    expect(result.current.isLoading).toBe(true);

    act(() => {
      result.current.setLoading(false);
    });

    expect(result.current.isLoading).toBe(false);
  });

  it('should clear trades', () => {
    const { result } = renderHook(() => useTradesStore());
    
    // Add some trades first
    act(() => {
      result.current.setTrades(mockTrades);
    });

    expect(result.current.trades).toHaveLength(2);

    // Clear trades
    act(() => {
      result.current.clearTrades();
    });

    expect(result.current.trades).toEqual([]);
  });

  it('should set analytics data', () => {
    const { result } = renderHook(() => useTradesStore());
    
    const mockAnalytics = {
      totalProfit: 300.00,
      winRate: 0.6,
      totalTrades: 10,
      avgProfit: 30.00
    };

    act(() => {
      result.current.setAnalytics(mockAnalytics);
    });

    expect(result.current.analytics).toEqual(mockAnalytics);
  });
});
import { configureStore } from '@reduxjs/toolkit';
import tradesReducer, { 
  fetchTrades, 
  addTrade, 
  updateTrade, 
  deleteTrade,
  setFilters,
  clearFilters 
} from '../trades';

const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      trades: tradesReducer,
    },
    preloadedState: {
      trades: {
        items: [],
        loading: false,
        error: null,
        filters: {},
        pagination: {
          page: 1,
          limit: 50,
          total: 0,
          totalPages: 0,
        },
        ...initialState,
      },
    },
  });
};

const mockTrade = {
  id: '1',
  symbol: 'AAPL',
  entry_time: '2024-01-01T10:00:00Z',
  exit_time: '2024-01-01T11:00:00Z',
  quantity: 100,
  entry_price: 150.00,
  exit_price: 155.00,
  pnl: 500.00,
  strategy: 'momentum',
  confidence_score: 8,
};

describe('Trades Slice', () => {
  let store: ReturnType<typeof createMockStore>;

  beforeEach(() => {
    store = createMockStore();
  });

  describe('fetchTrades action', () => {
    it('should handle fetchTrades.pending', () => {
      store.dispatch(fetchTrades.pending('', undefined));
      
      const state = store.getState().trades;
      expect(state.loading).toBe(true);
      expect(state.error).toBe(null);
    });

    it('should handle fetchTrades.fulfilled', () => {
      const mockResponse = {
        trades: [mockTrade],
        pagination: {
          page: 1,
          limit: 50,
          total: 1,
          totalPages: 1,
        },
      };

      store.dispatch(fetchTrades.fulfilled(mockResponse, '', undefined));
      
      const state = store.getState().trades;
      expect(state.loading).toBe(false);
      expect(state.items).toEqual([mockTrade]);
      expect(state.pagination).toEqual(mockResponse.pagination);
    });

    it('should handle fetchTrades.rejected', () => {
      const error = { message: 'Failed to fetch trades' };
      store.dispatch(fetchTrades.rejected(error as any, '', undefined));
      
      const state = store.getState().trades;
      expect(state.loading).toBe(false);
      expect(state.error).toBe('Failed to fetch trades');
    });
  });

  describe('addTrade action', () => {
    it('should add new trade to state', () => {
      store.dispatch(addTrade.fulfilled(mockTrade, '', mockTrade));
      
      const state = store.getState().trades;
      expect(state.items).toContain(mockTrade);
      expect(state.loading).toBe(false);
    });
  });

  describe('updateTrade action', () => {
    it('should update existing trade in state', () => {
      const initialState = { items: [mockTrade] };
      store = createMockStore(initialState);

      const updatedTrade = { ...mockTrade, pnl: 600.00 };
      store.dispatch(updateTrade.fulfilled(updatedTrade, '', { id: '1', data: updatedTrade }));
      
      const state = store.getState().trades;
      expect(state.items[0].pnl).toBe(600.00);
    });
  });

  describe('deleteTrade action', () => {
    it('should remove trade from state', () => {
      const initialState = { items: [mockTrade] };
      store = createMockStore(initialState);

      store.dispatch(deleteTrade.fulfilled('1', '', '1'));
      
      const state = store.getState().trades;
      expect(state.items).toHaveLength(0);
    });
  });

  describe('filter actions', () => {
    it('should set filters', () => {
      const filters = { symbol: 'AAPL', strategy: 'momentum' };
      store.dispatch(setFilters(filters));
      
      const state = store.getState().trades;
      expect(state.filters).toEqual(filters);
    });

    it('should clear filters', () => {
      const initialState = { filters: { symbol: 'AAPL' } };
      store = createMockStore(initialState);

      store.dispatch(clearFilters());
      
      const state = store.getState().trades;
      expect(state.filters).toEqual({});
    });
  });
});
import { configureStore } from '@reduxjs/toolkit';
import tradesReducer, { 
  setTrades, 
  addTrade, 
  updateTrade, 
  deleteTrade,
  setLoading,
  setError 
} from '../trades';

describe('trades slice', () => {
  let store: any;

  beforeEach(() => {
    store = configureStore({
      reducer: { trades: tradesReducer },
    });
  });

  const mockTrade = {
    id: '1',
    symbol: 'AAPL',
    entry_price: 150.00,
    exit_price: 155.00,
    quantity: 100,
    entry_time: '2024-01-01T10:00:00Z',
    exit_time: '2024-01-01T15:00:00Z',
    pnl: 500.00,
    tags: ['momentum'],
    playbook: 'breakout',
  };

  it('should handle initial state', () => {
    expect(store.getState().trades).toEqual({
      trades: [],
      isLoading: false,
      error: null,
      totalPnl: 0,
      winRate: 0,
    });
  });

  it('should handle setTrades', () => {
    const trades = [mockTrade];
    store.dispatch(setTrades(trades));
    
    expect(store.getState().trades.trades).toEqual(trades);
    expect(store.getState().trades.totalPnl).toBe(500);
  });

  it('should handle addTrade', () => {
    store.dispatch(addTrade(mockTrade));
    
    expect(store.getState().trades.trades).toHaveLength(1);
    expect(store.getState().trades.trades[0]).toEqual(mockTrade);
  });

  it('should handle updateTrade', () => {
    store.dispatch(addTrade(mockTrade));
    
    const updatedTrade = { ...mockTrade, exit_price: 160.00, pnl: 1000.00 };
    store.dispatch(updateTrade({ id: '1', updates: updatedTrade }));
    
    expect(store.getState().trades.trades[0].exit_price).toBe(160.00);
    expect(store.getState().trades.trades[0].pnl).toBe(1000.00);
  });

  it('should handle deleteTrade', () => {
    store.dispatch(addTrade(mockTrade));
    store.dispatch(deleteTrade('1'));
    
    expect(store.getState().trades.trades).toHaveLength(0);
  });

  it('should calculate win rate correctly', () => {
    const winningTrade = { ...mockTrade, id: '1', pnl: 500 };
    const losingTrade = { ...mockTrade, id: '2', pnl: -200 };
    
    store.dispatch(setTrades([winningTrade, losingTrade]));
    
    expect(store.getState().trades.winRate).toBe(50); // 1 winner out of 2 trades
  });
});
