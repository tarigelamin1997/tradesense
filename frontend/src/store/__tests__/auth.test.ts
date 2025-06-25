
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
