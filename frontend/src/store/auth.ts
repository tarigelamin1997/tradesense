
import { create } from 'zustand';
import { authService, LoginRequest, RegisterRequest } from '../services/auth';
import { User } from '../types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: authService.getCurrentUserFromStorage(),
  isAuthenticated: authService.isAuthenticated(),
  isLoading: false,
  error: null,

  login: async (credentials: LoginRequest) => {
    set({ isLoading: true, error: null });
    try {
      const tokenData = await authService.login(credentials);
      set({ 
        user: tokenData.user,
        isAuthenticated: true,
        isLoading: false 
      });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'Login failed',
        isLoading: false 
      });
      throw error;
    }
  },

  register: async (userData: RegisterRequest) => {
    set({ isLoading: true, error: null });
    try {
      await authService.register(userData);
      set({ isLoading: false });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'Registration failed',
        isLoading: false 
      });
      throw error;
    }
  },

  logout: async () => {
    set({ isLoading: true });
    try {
      await authService.logout();
      set({ 
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null 
      });
    } catch (error) {
      // Still clear local state even if API call fails
      set({ 
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null 
      });
    }
  },

  checkAuth: async () => {
    if (!authService.isAuthenticated()) {
      set({ user: null, isAuthenticated: false });
      return;
    }

    set({ isLoading: true });
    try {
      const isValid = await authService.checkAndRefreshToken();
      if (isValid) {
        const user = await authService.getCurrentUser();
        set({ 
          user,
          isAuthenticated: true,
          isLoading: false 
        });
      } else {
        set({ 
          user: null,
          isAuthenticated: false,
          isLoading: false 
        });
      }
    } catch (error) {
      set({ 
        user: null,
        isAuthenticated: false,
        isLoading: false 
      });
    }
  },

  clearError: () => set({ error: null }),
  
  setUser: (user: User | null) => set({ user, isAuthenticated: !!user })
}));
