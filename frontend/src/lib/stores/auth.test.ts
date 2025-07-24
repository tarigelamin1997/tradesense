import { describe, it, expect, beforeEach, vi } from 'vitest';
import { get } from 'svelte/store';
import { auth } from './auth';

// Mock browser environment
vi.mock('$app/environment', () => ({
	browser: true
}));

// Mock navigation
const mockGoto = vi.fn();
vi.mock('$app/navigation', () => ({
	goto: mockGoto
}));

// Mock API
const mockApi = {
	setAuthToken: vi.fn(),
	clearAuthToken: vi.fn(),
	post: vi.fn(),
	get: vi.fn()
};

vi.mock('$lib/api/ssr-safe', () => ({
	api: mockApi
}));

describe('Auth Store', () => {
	beforeEach(() => {
		// Clear mocks
		vi.clearAllMocks();
		
		// Clear localStorage
		localStorage.clear();
		
		// Reset auth store
		auth.logout();
	});

	describe('initialization', () => {
		it('should initialize with default state', () => {
			const state = get(auth);
			expect(state.user).toBeNull();
			expect(state.token).toBeNull();
			expect(state.loading).toBe(true);
			expect(state.initialized).toBe(false);
		});

		it('should load user from localStorage on initialize', async () => {
			const mockUser = {
				id: '123',
				email: 'test@example.com',
				name: 'Test User',
				subscription_tier: 'free' as const
			};
			const mockToken = 'test-token';

			localStorage.setItem('auth_token', mockToken);
			localStorage.setItem('user', JSON.stringify(mockUser));

			await auth.initialize();

			const state = get(auth);
			expect(state.user).toEqual(mockUser);
			expect(state.token).toBe(mockToken);
			expect(state.loading).toBe(false);
			expect(state.initialized).toBe(true);
			expect(mockApi.setAuthToken).toHaveBeenCalledWith(mockToken);
		});
	});

	describe('login', () => {
		it('should login successfully with valid credentials', async () => {
			const mockUser = {
				id: '123',
				email: 'test@example.com',
				name: 'Test User',
				subscription_tier: 'free' as const
			};
			const mockToken = 'test-token';

			mockApi.post.mockResolvedValueOnce({
				data: {
					user: mockUser,
					token: mockToken
				}
			});

			const result = await auth.login('test@example.com', 'password');

			expect(result.success).toBe(true);
			expect(result.user).toEqual(mockUser);
			
			const state = get(auth);
			expect(state.user).toEqual(mockUser);
			expect(state.token).toBe(mockToken);
			expect(state.loading).toBe(false);
			
			expect(localStorage.getItem('auth_token')).toBe(mockToken);
			expect(localStorage.getItem('user')).toBe(JSON.stringify(mockUser));
			expect(mockApi.setAuthToken).toHaveBeenCalledWith(mockToken);
		});

		it('should handle login failure', async () => {
			mockApi.post.mockRejectedValueOnce({
				response: {
					data: {
						detail: 'Invalid credentials'
					}
				}
			});

			const result = await auth.login('test@example.com', 'wrong-password');

			expect(result.success).toBe(false);
			expect(result.error).toBe('Invalid credentials');
			
			const state = get(auth);
			expect(state.user).toBeNull();
			expect(state.token).toBeNull();
		});
	});

	describe('logout', () => {
		it('should clear user data on logout', async () => {
			// Setup logged in state
			const mockUser = {
				id: '123',
				email: 'test@example.com',
				name: 'Test User',
				subscription_tier: 'free' as const
			};
			const mockToken = 'test-token';

			localStorage.setItem('auth_token', mockToken);
			localStorage.setItem('user', JSON.stringify(mockUser));
			await auth.initialize();

			// Logout
			await auth.logout();

			const state = get(auth);
			expect(state.user).toBeNull();
			expect(state.token).toBeNull();
			expect(state.loading).toBe(false);
			
			expect(localStorage.getItem('auth_token')).toBeNull();
			expect(localStorage.getItem('user')).toBeNull();
			expect(mockApi.clearAuthToken).toHaveBeenCalled();
			expect(mockGoto).toHaveBeenCalledWith('/login');
		});
	});

	describe('isAuthenticated derived store', () => {
		it('should return true when user is logged in', async () => {
			const mockUser = {
				id: '123',
				email: 'test@example.com',
				name: 'Test User',
				subscription_tier: 'free' as const
			};
			const mockToken = 'test-token';

			mockApi.post.mockResolvedValueOnce({
				data: { user: mockUser, token: mockToken }
			});

			await auth.login('test@example.com', 'password');

			const isAuth = get(auth.isAuthenticated);
			expect(isAuth).toBe(true);
		});

		it('should return false when user is not logged in', () => {
			const isAuth = get(auth.isAuthenticated);
			expect(isAuth).toBe(false);
		});
	});

	describe('refresh token', () => {
		it('should refresh token successfully', async () => {
			const newToken = 'new-token';
			const mockUser = {
				id: '123',
				email: 'test@example.com',
				name: 'Test User',
				subscription_tier: 'free' as const
			};

			// Setup initial auth state
			localStorage.setItem('auth_token', 'old-token');
			localStorage.setItem('user', JSON.stringify(mockUser));
			await auth.initialize();

			mockApi.post.mockResolvedValueOnce({
				data: { token: newToken }
			});

			await auth.refreshToken();

			const state = get(auth);
			expect(state.token).toBe(newToken);
			expect(localStorage.getItem('auth_token')).toBe(newToken);
			expect(mockApi.setAuthToken).toHaveBeenCalledWith(newToken);
		});
	});
});