import { configureStore } from '@reduxjs/toolkit';
import tradesReducer, { fetchTrades, addTrade } from '../trades';

const createTestStore = () => {
  return configureStore({
    reducer: {
      trades: tradesReducer
    }
  });
};

describe('Trades Store', () => {
  let store: ReturnType<typeof createTestStore>;

  beforeEach(() => {
    store = createTestStore();
  });

  it('should handle initial state', () => {
    const state = store.getState().trades;
    expect(state.trades).toEqual([]);
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('should handle fetch trades pending', () => {
    store.dispatch(fetchTrades.pending('', undefined));
    const state = store.getState().trades;
    expect(state.loading).toBe(true);
  });

  it('should handle fetch trades fulfilled', () => {
    const mockTrades = [
      { id: 1, symbol: 'AAPL', entry_price: 150, exit_price: 155, pnl: 500 }
    ];

    store.dispatch(fetchTrades.fulfilled(mockTrades, '', undefined));
    const state = store.getState().trades;

    expect(state.trades).toEqual(mockTrades);
    expect(state.loading).toBe(false);
  });

  it('should handle add trade', () => {
    const newTrade = { id: 2, symbol: 'GOOGL', entry_price: 2500, exit_price: 2600, pnl: 1000 };

    store.dispatch(addTrade.fulfilled(newTrade, '', newTrade));
    const state = store.getState().trades;

    expect(state.trades).toContain(newTrade);
  });
});