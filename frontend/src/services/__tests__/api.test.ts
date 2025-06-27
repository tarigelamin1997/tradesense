
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
import { api } from '../api';

// Mock fetch
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

describe('API Service', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('GET requests', () => {
    it('should make successful GET request', async () => {
      const mockData = { id: 1, name: 'Test' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      } as Response);

      const result = await api.get('/test');
      
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/test',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result).toEqual(mockData);
    });

    it('should handle GET request errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      } as Response);

      await expect(api.get('/nonexistent')).rejects.toThrow('HTTP error! status: 404');
    });
  });

  describe('POST requests', () => {
    it('should make successful POST request with data', async () => {
      const mockData = { id: 1, name: 'Created' };
      const postData = { name: 'New Item' };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      } as Response);

      const result = await api.post('/test', postData);
      
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/test',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(postData),
        })
      );
      expect(result).toEqual(mockData);
    });
  });

  describe('Authentication', () => {
    it('should include authorization header when token is present', async () => {
      localStorage.setItem('token', 'test-token');
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      } as Response);

      await api.get('/protected');
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        })
      );
      
      localStorage.removeItem('token');
    });
  });
});
