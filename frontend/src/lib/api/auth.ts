import { api } from './client';
import { writable, derived } from 'svelte/store';
import type { Readable, Writable } from 'svelte/store';
import { browser } from '$app/environment';

export interface User {
	id: string;
	email: string;
	username: string;
	created_at: string;
}

export interface LoginRequest {
	username: string;
	password: string;
}

export interface RegisterRequest {
	email: string;
	username: string;
	password: string;
}

export interface AuthResponse {
	access_token: string;
	token_type: string;
	user: User;
}

// Create auth store
interface AuthState {
	user: User | null;
	loading: boolean;
	error: string | null;
}

function createAuthStore() {
	const { subscribe, set, update }: Writable<AuthState> = writable({
		user: null,
		loading: false, // Set to false by default for SSR
		error: null
	});

	return {
		subscribe,
		
		async login(credentials: LoginRequest) {
			update(state => ({ ...state, loading: true, error: null }));
			
			try {
				// Send as JSON
				const response = await api.post<any>('/api/v1/auth/login', {
					username: credentials.username,
					password: credentials.password
				});
				
				console.log('Login response:', response);
				
				if (response.access_token) {
					api.setAuthToken(response.access_token);
					
					// Get user info after login
					const userInfo = await api.get<User>('/api/v1/auth/me');
					
					update(state => ({
						...state,
						user: userInfo,
						loading: false,
						error: null
					}));
					
					return { access_token: response.access_token, token_type: 'bearer', user: userInfo };
				}
				
				throw new Error('No access token received');
			} catch (error: any) {
				update(state => ({
					...state,
					user: null,
					loading: false,
					error: error.message || 'Login failed'
				}));
				throw error;
			}
		},
		
		async register(data: RegisterRequest) {
			update(state => ({ ...state, loading: true, error: null }));
			
			try {
				console.log('Attempting to register with:', data);
				// Register just creates the user
				const registerResponse = await api.post<any>('/api/v1/auth/register', data);
				console.log('Registration successful:', registerResponse);
				
				// Now login to get the token
				const loginResponse = await this.login({
					username: data.username,
					password: data.password
				});
				
				return loginResponse;
			} catch (error: any) {
				console.error('Registration error:', error);
				// Check if it's a validation error from backend
				let errorMessage = 'Registration failed';
				if (error.detail?.details?.message) {
					errorMessage = error.detail.details.message;
				} else if (error.message) {
					errorMessage = error.message;
				}
				
				update(state => ({
					...state,
					user: null,
					loading: false,
					error: errorMessage
				}));
				throw error;
			}
		},
		
		async logout() {
			api.clearAuth();
			set({ user: null, loading: false, error: null });
		},
		
		async checkAuth() {
			// Don't run on server
			if (!browser) {
				set({ user: null, loading: false, error: null });
				return;
			}
			
			if (!api.isAuthenticated()) {
				set({ user: null, loading: false, error: null });
				return;
			}
			
			update(state => ({ ...state, loading: true }));
			
			try {
				const user = await api.get<User>('/api/v1/auth/me');
				update(state => ({
					...state,
					user,
					loading: false,
					error: null
				}));
			} catch (error) {
				api.clearAuth();
				set({ user: null, loading: false, error: null });
			}
		},
		
		clearError() {
			update(state => ({ ...state, error: null }));
		}
	};
}

export const auth = createAuthStore();

// Derived store for authentication status
export const isAuthenticated: Readable<boolean> = derived(
	auth,
	$auth => !!$auth.user
);

// Email verification and password reset API
export const authApi = {
	async verifyEmail(token: string) {
		return api.post('/api/v1/auth/verify-email', null, { params: { token } });
	},
	
	async resendVerification(email: string) {
		return api.post('/api/v1/auth/resend-verification', null, { params: { email } });
	},
	
	async requestPasswordReset(email: string) {
		return api.post('/api/v1/auth/password-reset', { email });
	},
	
	async resetPassword(token: string, newPassword: string) {
		return api.post('/api/v1/auth/password-reset/confirm', {
			token,
			new_password: newPassword
		});
	}
};