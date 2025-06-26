import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import authSlice from '../../store/auth';
import LoginPage from '../../features/auth/pages/LoginPage';

// Mock store setup
const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authSlice
    },
    preloadedState: {
      auth: {
        user: null,
        token: null,
        isLoading: false,
        error: null,
        ...initialState
      }
    }
  });
};

// Wrapper component for tests
const TestWrapper: React.FC<{ children: React.ReactNode; store?: any }> = ({ 
  children, 
  store = createMockStore() 
}) => (
  <Provider store={store}>
    <BrowserRouter>
      {children}
    </BrowserRouter>
  </Provider>
);

describe('Auth Flow Integration Tests', () => {
  beforeEach(() => {
    // Reset fetch mock
    (global.fetch as jest.Mock).mockClear();
  });

  test('user can complete login flow successfully', async () => {
    // Mock successful login response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: 'mock_token',
        token_type: 'bearer',
        user: {
          id: '1',
          username: 'testuser',
          email: 'test@example.com'
        }
      })
    });

    const store = createMockStore();

    render(
      <TestWrapper store={store}>
        <LoginPage />
      </TestWrapper>
    );

    // Find form elements
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /login/i });

    // Fill out form
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    // Submit form
    fireEvent.click(submitButton);

    // Wait for API call
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/auth/login'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify({
            username: 'testuser',
            password: 'password123'
          })
        })
      );
    });

    // Check that store state was updated
    const state = store.getState();
    expect(state.auth.token).toBe('mock_token');
    expect(state.auth.user?.username).toBe('testuser');
  });

  test('displays error message on login failure', async () => {
    // Mock failed login response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: async () => ({
        detail: 'Invalid credentials'
      })
    });

    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /login/i });

    fireEvent.change(usernameInput, { target: { value: 'wronguser' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpass' } });
    fireEvent.click(submitButton);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  test('form validation works correctly', async () => {
    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: /login/i });

    // Try to submit empty form
    fireEvent.click(submitButton);

    // Check for validation messages
    await waitFor(() => {
      expect(screen.getByText(/username is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });

    // Verify no API call was made
    expect(global.fetch).not.toHaveBeenCalled();
  });
});