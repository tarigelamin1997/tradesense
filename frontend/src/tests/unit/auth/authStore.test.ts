import { describe, it, expect, beforeEach, vi } from 'vitest';
import { authStore } from '$lib/auth/authStore';
import type { User } from '$lib/types';

// Mock fetch
global.fetch = vi.fn();

describe('AuthStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state
    authStore.logout();
  });

  describe('login', () => {
    it('should login successfully with valid credentials', async () => {
      const mockUser: User = {
        id: '123',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
        subscription: 'free',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ user: mockUser })
      });

      const result = await authStore.login('test@example.com', 'password123');

      expect(result.success).toBe(true);
      expect(result.user).toEqual(mockUser);
      
      // Verify store state
      let currentUser;
      authStore.subscribe(state => { currentUser = state.user; })();
      expect(currentUser).toEqual(mockUser);

      // Verify fetch was called correctly
      expect(global.fetch).toHaveBeenCalledWith('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email: 'test@example.com', password: 'password123' })
      });
    });

    it('should handle login failure with invalid credentials', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Invalid credentials' })
      });

      const result = await authStore.login('test@example.com', 'wrongpassword');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid credentials');
      
      // Verify user is not set
      let currentUser;
      authStore.subscribe(state => { currentUser = state.user; })();
      expect(currentUser).toBeNull();
    });

    it('should handle network errors', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const result = await authStore.login('test@example.com', 'password123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Network error. Please try again.');
    });
  });

  describe('logout', () => {
    it('should logout successfully and clear user state', async () => {
      // Set initial user state
      const mockUser: User = {
        id: '123',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
        subscription: 'free',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      // Login first
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ user: mockUser })
      });
      await authStore.login('test@example.com', 'password123');

      // Mock logout response
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200
      });

      // Logout
      await authStore.logout();

      // Verify user is cleared
      let state;
      authStore.subscribe(s => { state = s; })();
      expect(state.user).toBeNull();
      expect(state.loading).toBe(false);

      // Verify logout API was called
      expect(global.fetch).toHaveBeenLastCalledWith('/api/auth/logout', {
        method: 'POST',
        credentials: 'include'
      });
    });
  });

  describe('checkAuth', () => {
    it('should check authentication status and update user', async () => {
      const mockUser: User = {
        id: '123',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
        subscription: 'pro',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ user: mockUser })
      });

      await authStore.checkAuth();

      // Verify user is set
      let currentUser;
      authStore.subscribe(state => { currentUser = state.user; })();
      expect(currentUser).toEqual(mockUser);

      // Verify API was called
      expect(global.fetch).toHaveBeenCalledWith('/api/auth/me', {
        credentials: 'include'
      });
    });

    it('should handle unauthenticated state', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401
      });

      await authStore.checkAuth();

      // Verify user is null
      let currentUser;
      authStore.subscribe(state => { currentUser = state.user; })();
      expect(currentUser).toBeNull();
    });
  });

  describe('updateProfile', () => {
    it('should update user profile successfully', async () => {
      const currentUser: User = {
        id: '123',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
        subscription: 'free',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      const updatedUser = {
        ...currentUser,
        name: 'Updated Name',
        email: 'updated@example.com'
      };

      // Set initial user
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ user: currentUser })
      });
      await authStore.login('test@example.com', 'password123');

      // Mock update response
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ user: updatedUser })
      });

      const result = await authStore.updateProfile({
        name: 'Updated Name',
        email: 'updated@example.com'
      });

      expect(result.success).toBe(true);
      expect(result.user).toEqual(updatedUser);

      // Verify user is updated in store
      let state;
      authStore.subscribe(s => { state = s; })();
      expect(state.user).toEqual(updatedUser);
    });
  });

  describe('permission checks', () => {
    it('should correctly check user permissions', async () => {
      const adminUser: User = {
        id: '123',
        email: 'admin@example.com',
        name: 'Admin User',
        role: 'admin',
        subscription: 'enterprise',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ user: adminUser })
      });
      await authStore.login('admin@example.com', 'password123');

      let state;
      authStore.subscribe(s => { state = s; })();
      
      expect(state.isAdmin).toBe(true);
      expect(state.hasProAccess).toBe(true);
    });

    it('should correctly identify free tier users', async () => {
      const freeUser: User = {
        id: '123',
        email: 'free@example.com',
        name: 'Free User',
        role: 'user',
        subscription: 'free',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ user: freeUser })
      });
      await authStore.login('free@example.com', 'password123');

      let state;
      authStore.subscribe(s => { state = s; })();
      
      expect(state.isAdmin).toBe(false);
      expect(state.hasProAccess).toBe(false);
    });
  });
});