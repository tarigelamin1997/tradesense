import { configureStore } from '@reduxjs/toolkit';
import authReducer, { login, logout, setUser } from '../auth';

const createTestStore = () => {
  return configureStore({
    reducer: {
      auth: authReducer
    }
  });
};

describe('Auth Store', () => {
  let store: ReturnType<typeof createTestStore>;

  beforeEach(() => {
    store = createTestStore();
  });

  it('should handle initial state', () => {
    const state = store.getState().auth;
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.loading).toBe(false);
  });

  it('should handle login pending', () => {
    store.dispatch(login.pending('', { email: 'test@example.com', password: 'password' }));
    const state = store.getState().auth;
    expect(state.loading).toBe(true);
  });

  it('should handle login fulfilled', () => {
    const mockResponse = {
      access_token: 'mock_token',
      user: { id: 1, email: 'test@example.com' }
    };

    store.dispatch(login.fulfilled(mockResponse, '', { email: 'test@example.com', password: 'password' }));
    const state = store.getState().auth;

    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual(mockResponse.user);
    expect(state.token).toBe('mock_token');
    expect(state.loading).toBe(false);
  });

  it('should handle logout', () => {
    // First login
    store.dispatch(setUser({ id: 1, email: 'test@example.com' }));

    // Then logout
    store.dispatch(logout());
    const state = store.getState().auth;

    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
  });
});