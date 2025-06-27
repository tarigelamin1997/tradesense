
import { renderHook, act } from '@testing-library/react';
import { useAuthStore } from '../auth';

// Mock localStorage
const mockLocalStorage = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; }
  };
})();

Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

describe('Auth Store', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.getState().logout();
  });

  it('should initialize with unauthenticated state', () => {
    const { result } = renderHook(() => useAuthStore());
    
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
  });

  it('should login user successfully', async () => {
    const { result } = renderHook(() => useAuthStore());
    
    const mockUser = { id: '1', email: 'test@example.com', name: 'Test User' };
    const mockToken = 'mock-jwt-token';

    await act(async () => {
      result.current.login(mockUser, mockToken);
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.token).toBe(mockToken);
    expect(localStorage.getItem('auth-token')).toBe(mockToken);
  });

  it('should logout user and clear storage', () => {
    const { result } = renderHook(() => useAuthStore());
    
    // First login
    act(() => {
      result.current.login({ id: '1', email: 'test@example.com', name: 'Test' }, 'token');
    });

    // Then logout
    act(() => {
      result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(localStorage.getItem('auth-token')).toBeNull();
  });

  it('should check auth from localStorage on init', () => {
    localStorage.setItem('auth-token', 'stored-token');
    localStorage.setItem('auth-user', JSON.stringify({ id: '1', email: 'stored@example.com' }));

    const { result } = renderHook(() => useAuthStore());
    
    act(() => {
      result.current.checkAuth();
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.token).toBe('stored-token');
  });
});
import { configureStore } from '@reduxjs/toolkit';
import authReducer, { login, logout, setToken, clearError } from '../auth';

const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
    },
    preloadedState: {
      auth: {
        isAuthenticated: false,
        user: null,
        token: null,
        loading: false,
        error: null,
        ...initialState,
      },
    },
  });
};

describe('Auth Slice', () => {
  let store: ReturnType<typeof createMockStore>;

  beforeEach(() => {
    store = createMockStore();
    localStorage.clear();
  });

  describe('login action', () => {
    it('should handle login.pending', () => {
      store.dispatch(login.pending('', { email: 'test@example.com', password: 'password' }));
      
      const state = store.getState().auth;
      expect(state.loading).toBe(true);
      expect(state.error).toBe(null);
    });

    it('should handle login.fulfilled', () => {
      const mockResponse = {
        user: { id: '1', email: 'test@example.com', name: 'Test User' },
        token: 'mock-jwt-token'
      };

      store.dispatch(login.fulfilled(mockResponse, '', { email: 'test@example.com', password: 'password' }));
      
      const state = store.getState().auth;
      expect(state.loading).toBe(false);
      expect(state.isAuthenticated).toBe(true);
      expect(state.user).toEqual(mockResponse.user);
      expect(state.token).toBe(mockResponse.token);
      expect(localStorage.setItem).toHaveBeenCalledWith('token', mockResponse.token);
    });

    it('should handle login.rejected', () => {
      const error = { message: 'Invalid credentials' };
      store.dispatch(login.rejected(error as any, '', { email: 'test@example.com', password: 'password' }));
      
      const state = store.getState().auth;
      expect(state.loading).toBe(false);
      expect(state.isAuthenticated).toBe(false);
      expect(state.error).toBe('Invalid credentials');
    });
  });

  describe('logout action', () => {
    it('should clear auth state and localStorage', () => {
      const initialState = {
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', name: 'Test User' },
        token: 'mock-token',
      };

      store = createMockStore(initialState);
      store.dispatch(logout());
      
      const state = store.getState().auth;
      expect(state.isAuthenticated).toBe(false);
      expect(state.user).toBe(null);
      expect(state.token).toBe(null);
      expect(localStorage.removeItem).toHaveBeenCalledWith('token');
    });
  });

  describe('setToken action', () => {
    it('should update token in state and localStorage', () => {
      const token = 'new-token';
      store.dispatch(setToken(token));
      
      const state = store.getState().auth;
      expect(state.token).toBe(token);
      expect(localStorage.setItem).toHaveBeenCalledWith('token', token);
    });
  });

  describe('clearError action', () => {
    it('should clear error state', () => {
      const initialState = { error: 'Some error' };
      store = createMockStore(initialState);
      
      store.dispatch(clearError());
      
      const state = store.getState().auth;
      expect(state.error).toBe(null);
    });
  });
});
import { configureStore } from '@reduxjs/toolkit';
import authReducer, { loginStart, loginSuccess, loginFailure, logout } from '../auth';

describe('auth slice', () => {
  let store: any;

  beforeEach(() => {
    store = configureStore({
      reducer: { auth: authReducer },
    });
  });

  it('should handle initial state', () => {
    expect(store.getState().auth).toEqual({
      user: null,
      token: null,
      isLoading: false,
      error: null,
    });
  });

  it('should handle login start', () => {
    store.dispatch(loginStart());
    expect(store.getState().auth.isLoading).toBe(true);
    expect(store.getState().auth.error).toBe(null);
  });

  it('should handle login success', () => {
    const mockUser = { id: '1', email: 'test@example.com' };
    const mockToken = 'mock-token';
    
    store.dispatch(loginSuccess({ user: mockUser, token: mockToken }));
    
    expect(store.getState().auth.user).toEqual(mockUser);
    expect(store.getState().auth.token).toBe(mockToken);
    expect(store.getState().auth.isLoading).toBe(false);
    expect(store.getState().auth.error).toBe(null);
  });

  it('should handle login failure', () => {
    const errorMessage = 'Login failed';
    
    store.dispatch(loginFailure(errorMessage));
    
    expect(store.getState().auth.error).toBe(errorMessage);
    expect(store.getState().auth.isLoading).toBe(false);
    expect(store.getState().auth.user).toBe(null);
  });

  it('should handle logout', () => {
    // First login
    store.dispatch(loginSuccess({ 
      user: { id: '1', email: 'test@example.com' }, 
      token: 'mock-token' 
    }));
    
    // Then logout
    store.dispatch(logout());
    
    expect(store.getState().auth.user).toBe(null);
    expect(store.getState().auth.token).toBe(null);
    expect(store.getState().auth.isLoading).toBe(false);
    expect(store.getState().auth.error).toBe(null);
  });
});
