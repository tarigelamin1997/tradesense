
import { authService } from '../auth';
import axios from 'axios';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('Auth Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('login', () => {
    it('should login successfully', async () => {
      const mockResponse = {
        data: {
          user: { id: '1', email: 'test@example.com', name: 'Test User' },
          token: 'mock-jwt-token'
        }
      };

      mockedAxios.post.mockResolvedValueOnce(mockResponse);

      const result = await authService.login('test@example.com', 'password123');

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/auth/login', {
        email: 'test@example.com',
        password: 'password123'
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle login error', async () => {
      const mockError = {
        response: {
          data: { message: 'Invalid credentials' },
          status: 401
        }
      };

      mockedAxios.post.mockRejectedValueOnce(mockError);

      await expect(authService.login('test@example.com', 'wrongpassword'))
        .rejects.toThrow('Invalid credentials');
    });
  });

  describe('register', () => {
    it('should register successfully', async () => {
      const mockResponse = {
        data: {
          user: { id: '1', email: 'new@example.com', name: 'New User' },
          token: 'new-jwt-token'
        }
      };

      mockedAxios.post.mockResolvedValueOnce(mockResponse);

      const result = await authService.register('new@example.com', 'password123', 'New User');

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/auth/register', {
        email: 'new@example.com',
        password: 'password123',
        name: 'New User'
      });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('logout', () => {
    it('should logout successfully', async () => {
      mockedAxios.post.mockResolvedValueOnce({ data: { message: 'Logged out' } });

      await authService.logout();

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/auth/logout');
    });
  });

  describe('refreshToken', () => {
    it('should refresh token successfully', async () => {
      const mockResponse = {
        data: { token: 'new-refreshed-token' }
      };

      mockedAxios.post.mockResolvedValueOnce(mockResponse);

      const result = await authService.refreshToken();

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/auth/refresh');
      expect(result).toEqual(mockResponse.data);
    });
  });
});
