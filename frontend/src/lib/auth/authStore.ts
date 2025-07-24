import { writable, derived } from 'svelte/store';
import type { User, AuthState } from '$lib/types';
import { goto } from '$app/navigation';

// Secure auth state management - NO tokens in localStorage
interface AuthStore extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  updateUser: (user: Partial<User>) => void;
}

function createAuthStore(): AuthStore {
  const { subscribe, set, update } = writable<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null
  });

  return {
    subscribe,
    
    async login(email: string, password: string) {
      update(state => ({ ...state, isLoading: true, error: null }));
      
      try {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include', // Important for httpOnly cookies
          body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.message || 'Login failed');
        }

        const { user } = await response.json();
        
        set({
          user,
          isAuthenticated: true,
          isLoading: false,
          error: null
        });

        await goto('/dashboard');
      } catch (error) {
        update(state => ({
          ...state,
          isLoading: false,
          error: error.message
        }));
      }
    },

    async logout() {
      try {
        await fetch('/api/auth/logout', {
          method: 'POST',
          credentials: 'include'
        });
      } catch (error) {
        console.error('Logout error:', error);
      }

      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null
      });

      await goto('/login');
    },

    async checkAuth() {
      try {
        const response = await fetch('/api/auth/me', {
          credentials: 'include'
        });

        if (response.ok) {
          const { user } = await response.json();
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } else {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          });
        }
      } catch (error) {
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: 'Network error'
        });
      }
    },

    updateUser(updates: Partial<User>) {
      update(state => ({
        ...state,
        user: state.user ? { ...state.user, ...updates } : null
      }));
    }
  };
}

export const auth = createAuthStore();

// Derived stores for specific auth states
export const isAuthenticated = derived(auth, $auth => $auth.isAuthenticated);
export const currentUser = derived(auth, $auth => $auth.user);
export const isLoading = derived(auth, $auth => $auth.isLoading);