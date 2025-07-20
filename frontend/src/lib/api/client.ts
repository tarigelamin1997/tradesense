import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import type { AxiosInstance, AxiosError } from 'axios';

// Use environment variable for API URL, fallback to empty string for Vite proxy
const API_BASE_URL = browser ? (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '') : '';
if (browser) {
	console.log('API Base URL:', API_BASE_URL || 'Using Vite proxy');
}

export interface ApiError {
	message: string;
	status: number;
	detail?: any;
}

class ApiClient {
	private client: AxiosInstance = null as any;
	private token: string | null = null;
	private initialized = false;

	constructor() {
		// Delay initialization until first use
	}

	private async initialize() {
		if (this.initialized || !browser) return;
		
		// Dynamically import axios only in browser
		const { default: axios } = await import('axios');
		
		this.client = axios.create({
			baseURL: API_BASE_URL,
			timeout: 30000,
			headers: {
				'Content-Type': 'application/json',
			},
		});

		// Load token from localStorage on init (client-side only)
		this.token = localStorage.getItem('authToken');

		this.setupInterceptors();
		this.initialized = true;
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

	getAuthToken(): string | null {
		return this.token;
	}

	// API methods
	async get<T>(url: string, params?: any): Promise<T> {
		await this.initialize();
		const response = await this.client.get<T>(url, { params });
		return response.data;
	}

	async post<T>(url: string, data?: any, config?: any): Promise<T> {
		await this.initialize();
		const response = await this.client.post<T>(url, data, config);
		return response.data;
	}

	async put<T>(url: string, data?: any): Promise<T> {
		await this.initialize();
		const response = await this.client.put<T>(url, data);
		return response.data;
	}

	async patch<T>(url: string, data?: any): Promise<T> {
		await this.initialize();
		const response = await this.client.patch<T>(url, data);
		return response.data;
	}

	async delete<T>(url: string): Promise<T> {
		await this.initialize();
		const response = await this.client.delete<T>(url);
		return response.data;
	}
}

// Export singleton instance with SSR-safe wrapper
let apiInstance: ApiClient | null = null;

// Create a mock API for SSR that returns safe defaults
const ssrApi: Partial<ApiClient> = {
	get: () => Promise.reject(new Error('API not available during SSR')),
	post: () => Promise.reject(new Error('API not available during SSR')),
	put: () => Promise.reject(new Error('API not available during SSR')),
	patch: () => Promise.reject(new Error('API not available during SSR')),
	delete: () => Promise.reject(new Error('API not available during SSR')),
	setAuthToken: () => {},
	clearAuth: () => {},
	getAuthToken: () => null,
	isAuthenticated: () => false
};

// Export a simple wrapper that checks browser at call time
export const api = {
	get<T = any>(...args: Parameters<ApiClient['get']>): ReturnType<ApiClient['get']> {
		if (!browser) return ssrApi.get!(...args);
		if (!apiInstance) apiInstance = new ApiClient();
		return apiInstance.get<T>(...args);
	},
	
	post<T = any>(...args: Parameters<ApiClient['post']>): ReturnType<ApiClient['post']> {
		if (!browser) return ssrApi.post!(...args);
		if (!apiInstance) apiInstance = new ApiClient();
		return apiInstance.post<T>(...args);
	},
	
	put<T = any>(...args: Parameters<ApiClient['put']>): ReturnType<ApiClient['put']> {
		if (!browser) return ssrApi.put!(...args);
		if (!apiInstance) apiInstance = new ApiClient();
		return apiInstance.put<T>(...args);
	},
	
	patch<T = any>(...args: Parameters<ApiClient['patch']>): ReturnType<ApiClient['patch']> {
		if (!browser) return ssrApi.patch!(...args);
		if (!apiInstance) apiInstance = new ApiClient();
		return apiInstance.patch<T>(...args);
	},
	
	delete<T = any>(...args: Parameters<ApiClient['delete']>): ReturnType<ApiClient['delete']> {
		if (!browser) return ssrApi.delete!(...args);
		if (!apiInstance) apiInstance = new ApiClient();
		return apiInstance.delete<T>(...args);
	},
	
	setAuthToken(token: string): void {
		if (!browser) return;
		if (!apiInstance) apiInstance = new ApiClient();
		apiInstance.setAuthToken(token);
	},
	
	clearAuth(): void {
		if (!browser) return;
		if (!apiInstance) apiInstance = new ApiClient();
		apiInstance.clearAuth();
	},
	
	getAuthToken(): string | null {
		if (!browser) return null;
		if (!apiInstance) apiInstance = new ApiClient();
		return apiInstance.getAuthToken();
	},
	
	isAuthenticated(): boolean {
		if (!browser) return false;
		if (!apiInstance) apiInstance = new ApiClient();
		return apiInstance.isAuthenticated();
	}
};

// Export types
export type { ApiClient };