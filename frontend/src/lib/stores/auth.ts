import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { api } from '$lib/api/ssr-safe';

interface User {
	id: string;
	email: string;
	name: string;
	subscription_tier: 'free' | 'starter' | 'professional' | 'enterprise';
	is_admin?: boolean;
	mfa_enabled?: boolean;
	created_at?: string;
	updated_at?: string;
}

interface AuthState {
	user: User | null;
	token: string | null;
	loading: boolean;
	initialized: boolean;
}

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>({
		user: null,
		token: null,
		loading: true,
		initialized: false
	});

	let refreshTimeout: NodeJS.Timeout;

	async function initialize() {
		if (!browser) return;

		const token = localStorage.getItem('auth_token');
		const userStr = localStorage.getItem('user');

		if (token && userStr) {
			try {
				const user = JSON.parse(userStr);
				api.setAuthToken(token);
				
				update(state => ({
					...state,
					user,
					token,
					loading: false,
					initialized: true
				}));

				// Verify token is still valid
				await checkAuth();
				
				// Schedule token refresh
				scheduleTokenRefresh();
			} catch (error) {
				console.error('Failed to initialize auth:', error);
				await logout();
			}
		} else {
			update(state => ({
				...state,
				loading: false,
				initialized: true
			}));
		}
	}

	async function login(email: string, password: string, mfaCode?: string) {
		try {
			const response = await api.post('/api/v1/auth/login', {
				email,
				password,
				mfa_code: mfaCode
			});

			const { access_token, user } = response.data;

			// Store auth data
			localStorage.setItem('auth_token', access_token);
			localStorage.setItem('user', JSON.stringify(user));
			
			// Set authorization header
			api.setAuthToken(access_token);

			update(state => ({
				...state,
				user,
				token: access_token,
				loading: false
			}));

			// Schedule token refresh
			scheduleTokenRefresh();

			return { success: true };
		} catch (error: any) {
			const message = error.response?.data?.detail || 'Login failed';
			return { 
				success: false, 
				error: message,
				requiresMfa: error.response?.status === 428
			};
		}
	}

	async function register(email: string, password: string, name: string) {
		try {
			const response = await api.post('/api/v1/auth/register', {
				email,
				password,
				name
			});

			const { access_token, user } = response.data;

			// Store auth data
			localStorage.setItem('auth_token', access_token);
			localStorage.setItem('user', JSON.stringify(user));
			
			// Set authorization header
			api.setAuthToken(access_token);

			update(state => ({
				...state,
				user,
				token: access_token,
				loading: false
			}));

			// Schedule token refresh
			scheduleTokenRefresh();

			return { success: true };
		} catch (error: any) {
			const message = error.response?.data?.detail || 'Registration failed';
			return { success: false, error: message };
		}
	}

	async function logout() {
		try {
			// Call logout endpoint
			await api.post('/api/v1/auth/logout');
		} catch (error) {
			console.error('Logout error:', error);
		} finally {
			// Clear local storage
			localStorage.removeItem('auth_token');
			localStorage.removeItem('user');
			
			// Clear auth header
			api.clearAuth();
			
			// Clear refresh timeout
			if (refreshTimeout) {
				clearTimeout(refreshTimeout);
			}

			// Reset store
			set({
				user: null,
				token: null,
				loading: false,
				initialized: true
			});

			// Redirect to login
			if (browser) {
				goto('/login');
			}
		}
	}

	async function checkAuth() {
		try {
			const response = await api.get('/api/v1/auth/me');
			const user = response.data;
			
			// Update user data
			localStorage.setItem('user', JSON.stringify(user));
			
			update(state => ({
				...state,
				user
			}));

			return true;
		} catch (error) {
			console.error('Auth check failed:', error);
			await logout();
			return false;
		}
	}

	async function refreshToken() {
		try {
			const response = await api.post('/api/v1/auth/refresh');
			const { access_token } = response.data;

			// Update token
			localStorage.setItem('auth_token', access_token);
			api.setAuthToken(access_token);

			update(state => ({
				...state,
				token: access_token
			}));

			// Schedule next refresh
			scheduleTokenRefresh();

			return true;
		} catch (error) {
			console.error('Token refresh failed:', error);
			await logout();
			return false;
		}
	}

	function scheduleTokenRefresh() {
		// Clear existing timeout
		if (refreshTimeout) {
			clearTimeout(refreshTimeout);
		}

		// Schedule refresh 5 minutes before token expires (25 minutes)
		refreshTimeout = setTimeout(() => {
			refreshToken();
		}, 25 * 60 * 1000);
	}

	async function updateUser(updates: Partial<User>) {
		try {
			const response = await api.patch('/api/v1/auth/me', updates);
			const user = response.data;

			// Update stored user
			localStorage.setItem('user', JSON.stringify(user));

			update(state => ({
				...state,
				user
			}));

			return { success: true };
		} catch (error: any) {
			const message = error.response?.data?.detail || 'Update failed';
			return { success: false, error: message };
		}
	}

	// IMPORTANT: Do not initialize automatically at module level
	// This prevents SSR errors on Vercel
	// Call authStore.initialize() from +layout.svelte onMount instead

	return {
		subscribe,
		login,
		register,
		logout,
		checkAuth,
		refreshToken,
		updateUser,
		initialize
	};
}

export const authStore = createAuthStore();

// Derived store for easy access to user
export const user = derived(authStore, $authStore => $authStore.user);

// Derived store for auth status
export const isAuthenticated = derived(authStore, $authStore => !!$authStore.user);

// Derived store for admin status
export const isAdmin = derived(authStore, $authStore => $authStore.user?.is_admin || false);