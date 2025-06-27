import { configureStore } from '@reduxjs/toolkit';
import authReducer, { login, logout, refreshToken, clearError } from '../auth';
import * as authService from '../../services/auth';

// Mock the auth service
jest.mock('../../services/auth');
const mockedAuthService = authService as jest.Mocked<typeof authService>;

describe('Auth Store', () => {
  let store: ReturnType<typeof configureStore>;

  beforeEach(() => {
    store = configureStore({
      reducer: {
        auth: authReducer,
      },
    });
    jest.clearAllMocks();
  });

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const state = store.getState().auth;
      expect(state).toEqual({
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        loading: false,
        error: null,
      });
    });
  });

  describe('login', () => {
    it('should handle successful login', async () => {
      const mockResponse = {
        user: { id: 1, email: 'test@example.com', name: 'Test User' },
        access_token: 'access-token',
        refresh_token: 'refresh-token',
      };

      mockedAuthService.login.mockResolvedValue(mockResponse);

      await store.dispatch(login({ email: 'test@example.com', password: 'password' }));

      const state = store.getState().auth;
      expect(state.user).toEqual(mockResponse.user);
      expect(state.token).toBe(mockResponse.access_token);
      expect(state.refreshToken).toBe(mockResponse.refresh_token);
      expect(state.isAuthenticated).toBe(true);
      expect(state.loading).toBe(false);
      expect(state.error).toBe(null);
    });

    it('should handle login failure', async () => {
      const mockError = new Error('Invalid credentials');
      mockedAuthService.login.mockRejectedValue(mockError);

      await store.dispatch(login({ email: 'test@example.com', password: 'wrong' }));

      const state = store.getState().auth;
      expect(state.user).toBe(null);
      expect(state.token).toBe(null);
      expect(state.isAuthenticated).toBe(false);
      expect(state.loading).toBe(false);
      expect(state.error).toBe('Invalid credentials');
    });

    it('should set loading state during login', () => {
      mockedAuthService.login.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      store.dispatch(login({ email: 'test@example.com', password: 'password' }));

      const state = store.getState().auth;
      expect(state.loading).toBe(true);
    });
  });

  describe('logout', () => {
    it('should clear auth state on logout', () => {
      // First set some auth state
      store.dispatch(login.fulfilled({
        user: { id: 1, email: 'test@example.com', name: 'Test User' },
        access_token: 'token',
        refresh_token: 'refresh',
      }, '', { email: 'test@example.com', password: 'password' }));

      // Then logout
      store.dispatch(logout());

      const state = store.getState().auth;
      expect(state.user).toBe(null);
      expect(state.token).toBe(null);
      expect(state.refreshToken).toBe(null);
      expect(state.isAuthenticated).toBe(false);
      expect(state.error).toBe(null);
    });
  });

  describe('refreshToken', () => {
    it('should update token on successful refresh', async () => {
      const mockResponse = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
      };

      mockedAuthService.refreshToken.mockResolvedValue(mockResponse);

      await store.dispatch(refreshToken('old-refresh-token'));

      const state = store.getState().auth;
      expect(state.token).toBe(mockResponse.access_token);
      expect(state.refreshToken).toBe(mockResponse.refresh_token);
    });

    it('should handle refresh token failure', async () => {
      const mockError = new Error('Token expired');
      mockedAuthService.refreshToken.mockRejectedValue(mockError);

      await store.dispatch(refreshToken('expired-token'));

      const state = store.getState().auth;
      expect(state.error).toBe('Token expired');
    });
  });

  describe('clearError', () => {
    it('should clear error state', () => {
      // Set error state first
      store.dispatch(login.rejected(new Error('Test error'), '', { email: '', password: '' }));

      // Clear error
      store.dispatch(clearError());

      const state = store.getState().auth;
      expect(state.error).toBe(null);
    });
  });
});