
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from '../../App';
import { useAuthStore } from '../../store/auth';
import { authService } from '../../services/auth';

// Mock the auth service
jest.mock('../../services/auth');
const mockedAuthService = authService as jest.Mocked<typeof authService>;

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

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Authentication Flow Integration', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.getState().logout();
    jest.clearAllMocks();
  });

  describe('Login Flow', () => {
    it('should login successfully and redirect to dashboard', async () => {
      const mockUser = { id: '1', email: 'test@example.com', name: 'Test User' };
      const mockToken = 'valid-jwt-token';

      mockedAuthService.login.mockResolvedValueOnce({
        user: mockUser,
        token: mockToken
      });

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      );

      // Should start at login page
      expect(screen.getByText('Login')).toBeInTheDocument();

      // Fill in login form
      fireEvent.change(screen.getByPlaceholderText(/email/i), {
        target: { value: 'test@example.com' }
      });
      fireEvent.change(screen.getByPlaceholderText(/password/i), {
        target: { value: 'password123' }
      });

      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

      // Wait for login to complete and redirect
      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
      });

      expect(mockedAuthService.login).toHaveBeenCalledWith('test@example.com', 'password123');
      expect(localStorage.getItem('auth-token')).toBe(mockToken);
    });

    it('should handle login error gracefully', async () => {
      mockedAuthService.login.mockRejectedValueOnce(new Error('Invalid credentials'));

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      );

      fireEvent.change(screen.getByPlaceholderText(/email/i), {
        target: { value: 'wrong@example.com' }
      });
      fireEvent.change(screen.getByPlaceholderText(/password/i), {
        target: { value: 'wrongpassword' }
      });

      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });

      // Should still be on login page
      expect(screen.getByText('Login')).toBeInTheDocument();
      expect(localStorage.getItem('auth-token')).toBeNull();
    });
  });

  describe('Token Refresh Flow', () => {
    it('should refresh expired token automatically', async () => {
      const expiredToken = 'expired-jwt-token';
      const newToken = 'refreshed-jwt-token';

      // Set expired token in localStorage
      localStorage.setItem('auth-token', expiredToken);

      mockedAuthService.getCurrentUser.mockRejectedValueOnce(new Error('Token expired'));
      mockedAuthService.refreshToken.mockResolvedValueOnce({ token: newToken });
      mockedAuthService.getCurrentUser.mockResolvedValueOnce({
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        createdAt: '2024-01-01',
        lastLogin: '2024-01-01'
      });

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockedAuthService.refreshToken).toHaveBeenCalled();
        expect(localStorage.getItem('auth-token')).toBe(newToken);
      });
    });

    it('should logout when token refresh fails', async () => {
      const expiredToken = 'expired-jwt-token';
      localStorage.setItem('auth-token', expiredToken);

      mockedAuthService.getCurrentUser.mockRejectedValueOnce(new Error('Token expired'));
      mockedAuthService.refreshToken.mockRejectedValueOnce(new Error('Refresh failed'));

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Login')).toBeInTheDocument();
        expect(localStorage.getItem('auth-token')).toBeNull();
      });
    });
  });

  describe('Logout Flow', () => {
    it('should logout and redirect to login page', async () => {
      const mockUser = { id: '1', email: 'test@example.com', name: 'Test User' };
      
      // Start with authenticated user
      useAuthStore.getState().login(mockUser, 'valid-token');

      mockedAuthService.logout.mockResolvedValueOnce({ message: 'Logged out' });

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      );

      // Should be on dashboard
      expect(screen.getByText('Dashboard')).toBeInTheDocument();

      // Find and click logout button
      const logoutButton = screen.getByRole('button', { name: /logout/i });
      fireEvent.click(logoutButton);

      await waitFor(() => {
        expect(screen.getByText('Login')).toBeInTheDocument();
      });

      expect(mockedAuthService.logout).toHaveBeenCalled();
      expect(localStorage.getItem('auth-token')).toBeNull();
    });
  });

  describe('Protected Routes', () => {
    it('should redirect unauthenticated users to login', async () => {
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      );

      // Should redirect to login page
      expect(screen.getByText('Login')).toBeInTheDocument();
    });

    it('should allow authenticated users to access protected routes', async () => {
      const mockUser = { id: '1', email: 'test@example.com', name: 'Test User' };
      
      // Set authenticated state
      useAuthStore.getState().login(mockUser, 'valid-token');

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      );

      // Should access dashboard
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing auth headers gracefully', async () => {
      localStorage.setItem('auth-token', 'invalid-format-token');

      mockedAuthService.getCurrentUser.mockRejectedValueOnce(new Error('Invalid token format'));

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Login')).toBeInTheDocument();
        expect(localStorage.getItem('auth-token')).toBeNull();
      });
    });

    it('should handle network errors during auth', async () => {
      localStorage.setItem('auth-token', 'valid-token');

      mockedAuthService.getCurrentUser.mockRejectedValueOnce(new Error('Network Error'));

      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });
  });
});
