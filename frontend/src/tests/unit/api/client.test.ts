import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ApiClient } from '$lib/api/client';
import type { User, Trade } from '$lib/types';

// Mock fetch
global.fetch = vi.fn();

// Mock window for event dispatching
global.window = {
  ...global.window,
  dispatchEvent: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn()
};

describe('ApiClient', () => {
  let apiClient: ApiClient;

  beforeEach(() => {
    vi.clearAllMocks();
    apiClient = new ApiClient();
  });

  describe('request method', () => {
    it('should make successful GET request', async () => {
      const mockData = { id: 1, name: 'Test' };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockData,
        headers: new Headers()
      });

      const result = await apiClient.get('/test');

      expect(result).toEqual(mockData);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:5173/api/test',
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      );
    });

    it('should handle query parameters', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({}),
        headers: new Headers()
      });

      await apiClient.get('/test', {
        params: { page: 1, limit: 10, search: 'query' }
      });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:5173/api/test?page=1&limit=10&search=query',
        expect.any(Object)
      );
    });

    it('should handle POST request with body', async () => {
      const postData = { name: 'New Item' };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({ id: 1, ...postData }),
        headers: new Headers()
      });

      const result = await apiClient.post('/items', postData);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:5173/api/items',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData),
          credentials: 'include'
        })
      );
    });

    it('should handle 401 unauthorized response', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Unauthorized' }),
        headers: new Headers()
      });

      await expect(apiClient.get('/protected')).rejects.toThrow('Unauthorized');
      expect(window.dispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'auth:unauthorized'
        })
      );
    });

    it('should handle 429 rate limit response', async () => {
      const retryAfter = '60';
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => ({ error: 'Rate limit exceeded' }),
        headers: new Headers({ 'Retry-After': retryAfter })
      });

      try {
        await apiClient.get('/test');
      } catch (error: any) {
        expect(error.message).toBe('Rate limit exceeded');
        expect(error.statusCode).toBe(429);
        expect(error.retryAfter).toBe(60);
      }
    });

    it('should timeout after specified duration', async () => {
      (global.fetch as any).mockImplementationOnce(() => 
        new Promise(resolve => setTimeout(resolve, 1000))
      );

      await expect(
        apiClient.get('/slow', { timeout: 100 })
      ).rejects.toThrow('Request timeout');
    });

    it('should handle network errors', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      await expect(apiClient.get('/test')).rejects.toThrow('Network error');
    });
  });

  describe('auth endpoints', () => {
    it('should login successfully', async () => {
      const mockUser: User = {
        id: '123',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
        subscription: 'pro',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ user: mockUser }),
        headers: new Headers()
      });

      const result = await apiClient.auth.login('test@example.com', 'password');

      expect(result.user).toEqual(mockUser);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ email: 'test@example.com', password: 'password' })
        })
      );
    });

    it('should logout successfully', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({}),
        headers: new Headers()
      });

      await apiClient.auth.logout();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/logout'),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });

    it('should get current user', async () => {
      const mockUser: User = {
        id: '123',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
        subscription: 'free',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ user: mockUser }),
        headers: new Headers()
      });

      const result = await apiClient.auth.me();

      expect(result.user).toEqual(mockUser);
    });
  });

  describe('trading endpoints', () => {
    it('should get trades with pagination', async () => {
      const mockTrades: Trade[] = [
        {
          id: '1',
          userId: '123',
          symbol: 'AAPL',
          type: 'buy',
          quantity: 100,
          price: 150,
          total: 15000,
          executedAt: new Date().toISOString(),
          status: 'completed',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          data: mockTrades,
          page: 1,
          pageSize: 10,
          total: 1
        }),
        headers: new Headers()
      });

      const result = await apiClient.trading.getTrades({ page: 1, pageSize: 10 });

      expect(result.data).toEqual(mockTrades);
      expect(result.page).toBe(1);
      expect(result.total).toBe(1);
    });

    it('should create a new trade', async () => {
      const newTrade = {
        symbol: 'AAPL',
        type: 'buy' as const,
        quantity: 100,
        price: 150
      };

      const createdTrade: Trade = {
        id: '123',
        userId: 'user123',
        ...newTrade,
        total: 15000,
        executedAt: new Date().toISOString(),
        status: 'completed',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => createdTrade,
        headers: new Headers()
      });

      const result = await apiClient.trading.createTrade(newTrade);

      expect(result).toEqual(createdTrade);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/trades'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(newTrade)
        })
      );
    });

    it('should delete a trade', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => null,
        headers: new Headers()
      });

      await apiClient.trading.deleteTrade('123');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/trades/123'),
        expect.objectContaining({
          method: 'DELETE'
        })
      );
    });
  });

  describe('error handling', () => {
    it('should parse error response correctly', async () => {
      const errorResponse = {
        error: 'Validation failed',
        details: {
          field: 'email',
          message: 'Invalid email format'
        }
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => errorResponse,
        headers: new Headers()
      });

      try {
        await apiClient.post('/users', { email: 'invalid' });
      } catch (error: any) {
        expect(error.message).toBe('Validation failed');
        expect(error.statusCode).toBe(400);
        expect(error.details).toEqual(errorResponse.details);
      }
    });

    it('should handle non-JSON error responses', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => { throw new Error('Invalid JSON'); },
        text: async () => 'Internal Server Error',
        headers: new Headers()
      });

      try {
        await apiClient.get('/test');
      } catch (error: any) {
        expect(error.message).toBe('Internal Server Error');
        expect(error.statusCode).toBe(500);
      }
    });
  });

  describe('request interceptors', () => {
    it('should add custom headers', async () => {
      apiClient = new ApiClient({
        headers: {
          'X-Custom-Header': 'test-value'
        }
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({}),
        headers: new Headers()
      });

      await apiClient.get('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Custom-Header': 'test-value'
          })
        })
      );
    });

    it('should use custom base URL', async () => {
      apiClient = new ApiClient({
        baseURL: 'https://api.example.com'
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({}),
        headers: new Headers()
      });

      await apiClient.get('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.example.com/test',
        expect.any(Object)
      );
    });
  });
});