
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
