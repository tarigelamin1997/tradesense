
import { setupServer } from 'msw/node';
import { rest } from 'msw';

export const handlers = [
  rest.post('/api/v1/auth/login', (req, res, ctx) => {
    return res(
      ctx.json({
        access_token: 'mock_token',
        token_type: 'bearer',
        user: { id: 1, email: 'test@example.com' }
      })
    );
  }),

  rest.get('/api/v1/trades', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: 1,
          symbol: 'AAPL',
          entry_price: 150.0,
          exit_price: 155.0,
          quantity: 100,
          pnl: 500.0,
          entry_time: '2025-01-01T10:00:00Z',
          exit_time: '2025-01-01T15:00:00Z'
        }
      ])
    );
  }),

  rest.get('/api/v1/analytics/performance', (req, res, ctx) => {
    return res(
      ctx.json({
        total_pnl: 10000,
        win_rate: 0.65,
        total_trades: 100,
        avg_win: 200,
        avg_loss: -150
      })
    );
  })
];

export const server = setupServer(...handlers);
