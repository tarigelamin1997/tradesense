import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import type { AuthUser } from '$lib/server/auth';

interface AuthState {
	user: AuthUser | null;
	loading: boolean;
	initialized: boolean;
}

function createSecureAuthStore() {
	const { subscribe, set, update } = writable<AuthState>({
		user: null,
		loading: true,
		initialized: false
	});

	let refreshTimeout: NodeJS.Timeout;

	return {
		subscribe,
		
		/**
		 * Initialize auth state from page data (SSR)
		 */
		initialize(user: AuthUser | null) {
			update(state => ({
				...state,
				user,
				loading: false,
				initialized: true
			}));
			
			// Schedule token refresh if authenticated
			if (user && browser) {
				this.scheduleRefresh();
			}
		},

		/**
		 * Login user using secure API endpoint
		 */
		async login(email: string, password: string) {
			try {
				update(state => ({ ...state, loading: true }));
				
				const response = await fetch('/api/auth/login', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify({ email, password }),
					credentials: 'include' // Important for cookies
				});

				const data = await response.json();
				
				if (!response.ok) {
					throw new Error(data.error || 'Login failed');
				}

				update(state => ({
					...state,
					user: data.user,
					loading: false
				}));
				
				// Schedule token refresh
				this.scheduleRefresh();
				
				// Navigate to dashboard
				await goto('/dashboard');
				
				return { success: true, user: data.user };
			} catch (error: any) {
				update(state => ({ ...state, loading: false }));
				return { 
					success: false, 
					error: error.message || 'Login failed' 
				};
			}
		},

		/**
		 * Logout user
		 */
		async logout() {
			try {
				await fetch('/api/auth/logout', {
					method: 'POST',
					credentials: 'include'
				});
			} catch (error) {
				console.error('Logout error:', error);
			}
			
			// Clear state
			set({
				user: null,
				loading: false,
				initialized: true
			});
			
			// Clear refresh timeout
			if (refreshTimeout) {
				clearTimeout(refreshTimeout);
			}
			
			// Navigate to login
			if (browser) {
				await goto('/login');
			}
		},

		/**
		 * Refresh authentication token
		 */
		async refreshToken() {
			try {
				const response = await fetch('/api/auth/refresh', {
					method: 'POST',
					credentials: 'include'
				});

				const data = await response.json();
				
				if (!response.ok) {
					throw new Error(data.error || 'Token refresh failed');
				}

				update(state => ({
					...state,
					user: data.user
				}));
				
				// Schedule next refresh
				this.scheduleRefresh();
				
				return true;
			} catch (error) {
				console.error('Token refresh failed:', error);
				
				// Logout on refresh failure
				await this.logout();
				return false;
			}
		},

		/**
		 * Schedule token refresh before expiry
		 */
		scheduleRefresh() {
			// Clear existing timeout
			if (refreshTimeout) {
				clearTimeout(refreshTimeout);
			}
			
			// Refresh token 5 minutes before expiry (assuming 1 hour tokens)
			const refreshIn = 55 * 60 * 1000; // 55 minutes
			
			refreshTimeout = setTimeout(() => {
				this.refreshToken();
			}, refreshIn);
		},

		/**
		 * Update user profile
		 */
		updateUser(user: AuthUser) {
			update(state => ({ ...state, user }));
		},

		/**
		 * Register new user
		 */
		async register(email: string, password: string, name: string) {
			try {
				update(state => ({ ...state, loading: true }));
				
				const response = await fetch('/api/auth/register', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify({ email, password, name }),
					credentials: 'include'
				});

				const data = await response.json();
				
				if (!response.ok) {
					throw new Error(data.error || 'Registration failed');
				}

				update(state => ({
					...state,
					user: data.user,
					loading: false
				}));
				
				// Schedule token refresh
				this.scheduleRefresh();
				
				// Navigate to dashboard
				await goto('/dashboard');
				
				return { success: true, user: data.user };
			} catch (error: any) {
				update(state => ({ ...state, loading: false }));
				return { 
					success: false, 
					error: error.message || 'Registration failed' 
				};
			}
		}
	};
}

export const secureAuth = createSecureAuthStore();

// Derived stores
export const isAuthenticated = derived(
	secureAuth,
	$auth => !!$auth.user && $auth.initialized
);

export const isLoading = derived(
	secureAuth,
	$auth => $auth.loading
);

export const currentUser = derived(
	secureAuth,
	$auth => $auth.user
);