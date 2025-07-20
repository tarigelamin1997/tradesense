import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';

// Use environment variable for API URL, fallback to empty string for Vite proxy
const API_BASE_URL = browser ? (import.meta.env.VITE_API_URL || '') : '';
if (browser) {
	console.log('API Base URL:', API_BASE_URL || 'Using Vite proxy');
}

export interface ApiError {
	message: string;
	status: number;
	detail?: any;
}

class ApiClient {
	private client: AxiosInstance;
	private token: string | null = null;

	constructor() {
		this.client = axios.create({
			baseURL: API_BASE_URL,
			timeout: 30000,
			headers: {
				'Content-Type': 'application/json',
			},
		});

		// Load token from localStorage on init (client-side only)
		if (browser) {
			this.token = localStorage.getItem('authToken');
		}

		this.setupInterceptors();
	}

	private setupInterceptors() {
		// Request interceptor to add auth token
		this.client.interceptors.request.use(
			(config) => {
				if (browser) {
					console.log('Making request to:', config.url);
					console.log('Base URL:', config.baseURL);
					console.log('Full URL:', config.baseURL + config.url);
				}
				if (this.token) {
					config.headers.Authorization = `Bearer ${this.token}`;
				}
				return config;
			},
			(error) => {
				return Promise.reject(error);
			}
		);

		// Response interceptor for error handling
		this.client.interceptors.response.use(
			(response) => response,
			async (error: AxiosError) => {
				console.error('API Error:', {
					url: error.config?.url,
					method: error.config?.method,
					status: error.response?.status,
					statusText: error.response?.statusText,
					data: error.response?.data,
					message: error.message
				});
				
				if (error.response?.status === 401) {
					// Clear token and redirect to login
					this.clearAuth();
					if (browser) {
						goto('/login');
					}
				}
				
				// Transform error for consistent handling
				const responseData = error.response?.data as any;
				const apiError: ApiError = {
					message: responseData?.detail || responseData?.message || error.message || 'An error occurred',
					status: error.response?.status || 500,
					detail: responseData
				};
				
				return Promise.reject(apiError);
			}
		);
	}

	// Auth methods
	setAuthToken(token: string) {
		this.token = token;
		if (browser) {
			localStorage.setItem('authToken', token);
		}
	}

	clearAuth() {
		this.token = null;
		if (browser) {
			localStorage.removeItem('authToken');
		}
	}

	isAuthenticated(): boolean {
		return !!this.token;
	}

	// API methods
	async get<T>(url: string, params?: any): Promise<T> {
		const response = await this.client.get<T>(url, { params });
		return response.data;
	}

	async post<T>(url: string, data?: any, config?: any): Promise<T> {
		const response = await this.client.post<T>(url, data, config);
		return response.data;
	}

	async put<T>(url: string, data?: any): Promise<T> {
		const response = await this.client.put<T>(url, data);
		return response.data;
	}

	async patch<T>(url: string, data?: any): Promise<T> {
		const response = await this.client.patch<T>(url, data);
		return response.data;
	}

	async delete<T>(url: string): Promise<T> {
		const response = await this.client.delete<T>(url);
		return response.data;
	}
}

// Export singleton instance
// Create a singleton instance that's SSR-safe
let apiInstance: ApiClient | null = null;

export const api = new Proxy({} as ApiClient, {
	get(target, prop) {
		if (!apiInstance && browser) {
			apiInstance = new ApiClient();
		}
		if (!apiInstance) {
			// Return no-op functions during SSR
			if (typeof prop === 'string' && ['get', 'post', 'put', 'patch', 'delete'].includes(prop)) {
				return () => Promise.reject(new Error('API not available during SSR'));
			}
			if (prop === 'setAuthToken' || prop === 'clearAuth' || prop === 'getAuthToken' || prop === 'isAuthenticated') {
				return () => {};
			}
			return undefined;
		}
		return apiInstance[prop as keyof ApiClient];
	}
});

// Export types
export type { ApiClient };