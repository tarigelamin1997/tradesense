import { api as apiClient } from './client';
import { writable, derived } from 'svelte/store';
import type { Readable, Writable } from 'svelte/store';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';

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
				// OAuth2 requires form data, not JSON
				const formData = new URLSearchParams();
				formData.append('username', credentials.username);
				formData.append('password', credentials.password);
				
				const apiUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';
				console.log('Attempting login to:', apiUrl);
				console.log('Username:', credentials.username);
				
				// Use the correct OAuth2 token endpoint with form data
				const loginUrl = `${apiUrl}/auth/token`;
				console.log('Login URL:', loginUrl);
				
				const response = await fetch(loginUrl, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/x-www-form-urlencoded'
					},
					body: formData.toString(),
					credentials: 'include'
				});
				
				if (!response.ok) {
					const errorData = await response.json().catch(() => ({}));
					console.error('Login failed:', response.status, response.statusText, errorData);
					throw new Error(errorData.detail || `Login failed: ${response.status} ${response.statusText}`);
				}
				
				const data = await response.json();
				console.log('Login response:', data);
				
				if (data.access_token) {
					// Store token in httpOnly cookie is handled by backend
					// Get user info after login
					const userResponse = await fetch(`${apiUrl}/auth/me`, {
						headers: {
							'Authorization': `Bearer ${data.access_token}`
						},
						credentials: 'include'
					});
					
					if (!userResponse.ok) {
						throw new Error('Failed to get user info');
					}
					
					const userInfo = await userResponse.json();
					
					update(state => ({
						...state,
						user: userInfo,
						loading: false,
						error: null
					}));
					
					return { 
						access_token: data.access_token, 
						token_type: 'bearer', 
						user: userInfo, 
						mfa_required: data.mfa_required, 
						session_id: data.session_id, 
						methods: data.methods 
					};
				}
				
				throw new Error('No access token received');
			} catch (error: any) {
				console.error('Login error:', error);
				console.error('Error details:', {
					name: error.name,
					message: error.message,
					stack: error.stack
				});
				
				let errorMessage = 'Login failed';
				
				if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
					errorMessage = `Unable to connect to server at ${apiUrl}. Please check if the backend is running and CORS is configured.`;
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
		
		async register(data: RegisterRequest) {
			update(state => ({ ...state, loading: true, error: null }));
			
			try {
				const apiUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';
				console.log('Attempting to register at:', apiUrl);
				console.log('Registration data:', data);
				
				// Register just creates the user
				const registerUrl = `${apiUrl}/auth/register`;
				console.log('Register URL:', registerUrl);
				
				const registerResponse = await fetch(registerUrl, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify(data),
					credentials: 'include'
				});
				
				if (!registerResponse.ok) {
					const errorData = await registerResponse.json().catch(() => ({}));
					console.error('Registration failed:', registerResponse.status, registerResponse.statusText, errorData);
					throw new Error(errorData.detail || `Registration failed: ${registerResponse.status} ${registerResponse.statusText}`);
				}
				
				console.log('Registration successful');
				
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
				} else if (error.detail && typeof error.detail === 'string') {
					errorMessage = error.detail;
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
			try {
				const apiUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';
				await fetch(`${apiUrl}/auth/logout`, {
					method: 'POST',
					credentials: 'include'
				});
			} catch (error) {
				console.error('Logout error:', error);
			}
			set({ user: null, loading: false, error: null });
			if (browser) {
				goto('/login');
			}
		},
		
		async checkAuth() {
			// Don't run on server
			if (!browser) {
				set({ user: null, loading: false, error: null });
				return;
			}
			
			update(state => ({ ...state, loading: true }));
			
			try {
				const apiUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';
				const response = await fetch(`${apiUrl}/auth/me`, {
					credentials: 'include'
				});
				
				if (!response.ok) {
					throw new Error('Not authenticated');
				}
				
				const user = await response.json();
				update(state => ({
					...state,
					user,
					loading: false,
					error: null
				}));
			} catch (error) {
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
		return apiClient.post('/auth/verify-email', null, { params: { token } });
	},
	
	async resendVerification(email: string) {
		return apiClient.post('/auth/resend-verification', null, { params: { email } });
	},
	
	async requestPasswordReset(email: string) {
		return apiClient.post('/auth/password-reset', { email });
	},
	
	async resetPassword(token: string, newPassword: string) {
		return apiClient.post('/auth/password-reset/confirm', {
			token,
			new_password: newPassword
		});
	}
};