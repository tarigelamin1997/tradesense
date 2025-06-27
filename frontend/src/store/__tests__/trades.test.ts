import { configureStore } from '@reduxjs/toolkit';
import tradesReducer, { 
  fetchTrades, 
  addTrade, 
  updateTrade, 
  deleteTrade,
  setFilters,
  clearFilters 
} from '../trades';
import * as tradesService from '../../services/trades';

// Mock the trades service
jest.mock('../../services/trades');
const mockedTradesService = tradesService as jest.Mocked<typeof tradesService>;

describe('Trades Store', () => {
  let store: ReturnType<typeof configureStore>;

  beforeEach(() => {
    store = configureStore({
      reducer: {
        trades: tradesReducer,
      },
    });
    jest.clearAllMocks();
  });

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const state = store.getState().trades;
      expect(state).toEqual({
        trades: [],
        loading: false,
        error: null,
        filters: {},
        pagination: {
          page: 1,
          limit: 50,
          total: 0,
        },
      });
    });
  });

  describe('fetchTrades', () => {
    it('should fetch trades successfully', async () => {
      const mockTrades = [
        {
          id: 1,
          symbol: 'AAPL',
          entry_price: 150.00,
          exit_price: 155.00,
          quantity: 100,
          trade_date: '2024-01-01',
          profit_loss: 500.00,
        },
      ];

      mockedTradesService.getTrades.mockResolvedValue({
        trades: mockTrades,
        total: 1,
        page: 1,
        limit: 50,
      });

      await store.dispatch(fetchTrades({ page: 1, limit: 50 }));

      const state = store.getState().trades;
      expect(state.trades).toEqual(mockTrades);
      expect(state.pagination.total).toBe(1);
      expect(state.loading).toBe(false);
      expect(state.error).toBe(null);
    });

    it('should handle fetch trades failure', async () => {
      const mockError = new Error('Failed to fetch trades');
      mockedTradesService.getTrades.mockRejectedValue(mockError);

      await store.dispatch(fetchTrades({ page: 1, limit: 50 }));

      const state = store.getState().trades;
      expect(state.trades).toEqual([]);
      expect(state.loading).toBe(false);
      expect(state.error).toBe('Failed to fetch trades');
    });
  });

  describe('addTrade', () => {
    it('should add trade successfully', async () => {
      const newTrade = {
        symbol: 'TSLA',
        entry_price: 200.00,
        exit_price: 210.00,
        quantity: 50,
        trade_date: '2024-01-02',
      };

      const createdTrade = { ...newTrade, id: 2, profit_loss: 500.00 };
      mockedTradesService.createTrade.mockResolvedValue(createdTrade);

      await store.dispatch(addTrade(newTrade));

      const state = store.getState().trades;
      expect(state.trades).toContain(createdTrade);
      expect(state.loading).toBe(false);
      expect(state.error).toBe(null);
    });
  });

  describe('updateTrade', () => {
    it('should update trade successfully', async () => {
      // First add a trade
      const initialTrade = {
        id: 1,
        symbol: 'AAPL',
        entry_price: 150.00,
        exit_price: 155.00,
        quantity: 100,
        trade_date: '2024-01-01',
        profit_loss: 500.00,
      };

      store.dispatch(fetchTrades.fulfilled({
        trades: [initialTrade],
        total: 1,
        page: 1,
        limit: 50,
      }, '', { page: 1, limit: 50 }));

      // Update the trade
      const updatedTrade = { ...initialTrade, exit_price: 160.00, profit_loss: 1000.00 };
      mockedTradesService.updateTrade.mockResolvedValue(updatedTrade);

      await store.dispatch(updateTrade({ id: 1, updates: { exit_price: 160.00 } }));

      const state = store.getState().trades;
      const trade = state.trades.find(t => t.id === 1);
      expect(trade?.exit_price).toBe(160.00);
      expect(trade?.profit_loss).toBe(1000.00);
    });
  });

  describe('deleteTrade', () => {
    it('should delete trade successfully', async () => {
      // First add trades
      const trades = [
        { id: 1, symbol: 'AAPL', profit_loss: 500.00 },
        { id: 2, symbol: 'TSLA', profit_loss: 300.00 },
      ];

      store.dispatch(fetchTrades.fulfilled({
        trades,
        total: 2,
        page: 1,
        limit: 50,
      }, '', { page: 1, limit: 50 }));

      mockedTradesService.deleteTrade.mockResolvedValue(undefined);

      await store.dispatch(deleteTrade(1));

      const state = store.getState().trades;
      expect(state.trades).toHaveLength(1);
      expect(state.trades.find(t => t.id === 1)).toBeUndefined();
    });
  });

  describe('filters', () => {
    it('should set filters', () => {
      const filters = { symbol: 'AAPL', date_from: '2024-01-01' };

      store.dispatch(setFilters(filters));

      const state = store.getState().trades;
      expect(state.filters).toEqual(filters);
    });

    it('should clear filters', () => {
      // Set filters first
      store.dispatch(setFilters({ symbol: 'AAPL' }));

      // Clear filters
      store.dispatch(clearFilters());

      const state = store.getState().trades;
      expect(state.filters).toEqual({});
    });
  });
});