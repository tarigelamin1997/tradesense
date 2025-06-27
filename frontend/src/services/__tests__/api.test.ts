
import { apiRequest, authApi, tradesApi } from '../api';

// Mock fetch
global.fetch = jest.fn();

const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

describe('API Service', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    localStorage.clear();
  });

  describe('apiRequest', () => {
    it('should make GET request successfully', async () => {
      const mockResponse = { data: 'test' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await apiRequest('/test');
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should include auth token when available', async () => {
      localStorage.setItem('token', 'mock-token');
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      } as Response);

      await apiRequest('/test');
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token',
          }),
        })
      );
    });

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(apiRequest('/test')).rejects.toThrow('Network error');
    });

    it('should handle HTTP errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      } as Response);

      await expect(apiRequest('/test')).rejects.toThrow('HTTP error! status: 404');
    });
  });

  describe('authApi', () => {
    it('should login successfully', async () => {
      const mockResponse = { token: 'auth-token', user: { id: '1' } };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await authApi.login('test@example.com', 'password');
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'password',
          }),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should register successfully', async () => {
      const mockResponse = { token: 'auth-token', user: { id: '1' } };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await authApi.register('Test User', 'test@example.com', 'password');
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/register'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            name: 'Test User',
            email: 'test@example.com',
            password: 'password',
          }),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('tradesApi', () => {
    beforeEach(() => {
      localStorage.setItem('token', 'mock-token');
    });

    it('should fetch trades successfully', async () => {
      const mockResponse = { trades: [], pagination: {} };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await tradesApi.getTrades();
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/trades'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token',
          }),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should create trade successfully', async () => {
      const newTrade = { symbol: 'AAPL', quantity: 100 };
      const mockResponse = { id: '1', ...newTrade };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await tradesApi.createTrade(newTrade);
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/trades'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(newTrade),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });
});
