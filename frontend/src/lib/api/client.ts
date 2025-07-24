import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import type { ApiError, ApiResponse } from '$lib/types';

// Use environment variable for API URL, fallback to empty string for Vite proxy
const API_BASE_URL = browser ? (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '') : '';

interface RequestOptions extends RequestInit {
	params?: Record<string, any>;
	timeout?: number;
}

class ApiClient {
	private defaultHeaders: Record<string, string> = {
		'Content-Type': 'application/json',
	};
	private requestInterceptors: Array<(config: RequestInit) => RequestInit> = [];
	private responseInterceptors: Array<(response: Response) => Response | Promise<Response>> = [];

	constructor() {
		this.setupInterceptors();
	}

	// Build URL with query params
	private buildUrl(endpoint: string, params?: Record<string, any>): string {
		const url = new URL(`${API_BASE_URL}${endpoint}`, window.location.origin);
		
		if (params) {
			Object.entries(params).forEach(([key, value]) => {
				if (value !== undefined && value !== null) {
					url.searchParams.append(key, String(value));
				}
			});
		}
		
		return url.toString();
	}

	// Apply request interceptors
	private applyRequestInterceptors(config: RequestInit): RequestInit {
		return this.requestInterceptors.reduce((acc, interceptor) => interceptor(acc), config);
	}

	// Apply response interceptors
	private async applyResponseInterceptors(response: Response): Promise<Response> {
		for (const interceptor of this.responseInterceptors) {
			response = await interceptor(response);
		}
		return response;
	}

	// Handle API errors
	private async handleError(response: Response): Promise<never> {
		let error: ApiError;
		
		try {
			const data = await response.json();
			error = {
				message: data.message || data.detail || 'An error occurred',
				code: data.code || 'UNKNOWN_ERROR',
				statusCode: response.status,
				details: data.details || data
			};
		} catch {
			error = {
				message: response.statusText || 'Network error',
				code: 'NETWORK_ERROR',
				statusCode: response.status,
				details: {}
			};
		}

		// Handle specific error codes
		if (response.status === 401) {
			// Trigger logout
			window.dispatchEvent(new CustomEvent('auth:unauthorized'));
			if (browser) {
				goto('/login');
			}
		} else if (response.status === 429) {
			// Rate limit hit
			window.dispatchEvent(new CustomEvent('api:rate-limit', { detail: error }));
		}
		
		throw error;
	}

	private setupInterceptors() {
		// Add CSRF token to requests
		this.requestInterceptors.push((config) => {
			const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
			if (csrfToken && config.headers) {
				(config.headers as Record<string, string>)['X-CSRF-Token'] = csrfToken;
			}
			return config;
		});

		// Add request ID for tracing
		this.requestInterceptors.push((config) => {
			if (config.headers) {
				(config.headers as Record<string, string>)['X-Request-ID'] = crypto.randomUUID();
			}
			return config;
		});
	}

	// Main request method
	private async request<T>(
		endpoint: string,
		options: RequestOptions = {}
	): Promise<T> {
		if (!browser) {
			throw new Error('API calls are not available during SSR');
		}

		const { params, timeout = 30000, ...fetchOptions } = options;
		
		// Build config
		let config: RequestInit = {
			...fetchOptions,
			headers: {
				...this.defaultHeaders,
				...fetchOptions.headers,
			},
			credentials: 'include', // Always include cookies for httpOnly auth
		};

		// Apply request interceptors
		config = this.applyRequestInterceptors(config);

		// Create abort controller for timeout
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), timeout);
		
		try {
			const response = await fetch(
				this.buildUrl(endpoint, params),
				{
					...config,
					signal: controller.signal
				}
			);

			clearTimeout(timeoutId);

			// Apply response interceptors
			const processedResponse = await this.applyResponseInterceptors(response);

			if (!processedResponse.ok) {
				await this.handleError(processedResponse);
			}

			// Handle empty responses
			if (processedResponse.status === 204) {
				return {} as T;
			}

			const data = await processedResponse.json();
			return data as T;
		} catch (error: any) {
			clearTimeout(timeoutId);
			
			if (error.name === 'AbortError') {
				throw {
					message: 'Request timeout',
					code: 'TIMEOUT',
					statusCode: 0,
					details: { timeout }
				} as ApiError;
			}
			
			throw error;
		}
	}

	// HTTP methods
	async get<T>(endpoint: string, params?: Record<string, any>, options?: RequestOptions): Promise<T> {
		return this.request<T>(endpoint, {
			...options,
			method: 'GET',
			params: { ...params, ...options?.params }
		});
	}

	async post<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
		return this.request<T>(endpoint, {
			...options,
			method: 'POST',
			body: data ? JSON.stringify(data) : undefined
		});
	}

	async put<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
		return this.request<T>(endpoint, {
			...options,
			method: 'PUT',
			body: data ? JSON.stringify(data) : undefined
		});
	}

	async patch<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
		return this.request<T>(endpoint, {
			...options,
			method: 'PATCH',
			body: data ? JSON.stringify(data) : undefined
		});
	}

	async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
		return this.request<T>(endpoint, {
			...options,
			method: 'DELETE'
		});
	}

	// File upload
	async upload<T>(endpoint: string, file: File, additionalData?: Record<string, any>): Promise<T> {
		const formData = new FormData();
		formData.append('file', file);
		
		if (additionalData) {
			Object.entries(additionalData).forEach(([key, value]) => {
				formData.append(key, String(value));
			});
		}

		return this.request<T>(endpoint, {
			method: 'POST',
			body: formData,
			headers: {
				// Remove Content-Type to let browser set it with boundary
			}
		});
	}
}

// Create singleton instance
export const api = browser ? new ApiClient() : {
	get: () => Promise.reject(new Error('API not available during SSR')),
	post: () => Promise.reject(new Error('API not available during SSR')),
	put: () => Promise.reject(new Error('API not available during SSR')),
	patch: () => Promise.reject(new Error('API not available during SSR')),
	delete: () => Promise.reject(new Error('API not available during SSR')),
	upload: () => Promise.reject(new Error('API not available during SSR'))
};

// Export typed API methods for better DX
export const tradingApi = {
	// Trades
	getTrades: (params?: Record<string, any>) => 
		api.get<PaginatedResponse<Trade>>('/api/trades', params),
	
	getTrade: (id: string) => 
		api.get<Trade>(`/api/trades/${id}`),
	
	createTrade: (trade: Partial<Trade>) => 
		api.post<Trade>('/api/trades', trade),
	
	updateTrade: (id: string, updates: Partial<Trade>) => 
		api.patch<Trade>(`/api/trades/${id}`, updates),
	
	deleteTrade: (id: string) => 
		api.delete<void>(`/api/trades/${id}`),

	// Analytics
	getAnalytics: (params?: { startDate?: string; endDate?: string }) => 
		api.get<Analytics>('/api/analytics', params),
	
	getPortfolio: () => 
		api.get<Portfolio>('/api/portfolio'),

	// Import
	importCSV: (file: File) => 
		api.upload<{ imported: number; failed: number }>('/api/import/csv', file),
};

// Export auth API methods
export const authApi = {
	login: (email: string, password: string) => 
		api.post<{ user: User }>('/api/auth/login', { email, password }),
	
	logout: () => 
		api.post<void>('/api/auth/logout'),
	
	register: (data: { email: string; password: string; name: string }) => 
		api.post<{ user: User }>('/api/auth/register', data),
	
	getCurrentUser: () => 
		api.get<{ user: User }>('/api/auth/me'),
	
	updateProfile: (updates: Partial<User>) => 
		api.patch<{ user: User }>('/api/auth/profile', updates),
};

// Import types
import type { 
	Trade, Analytics, Portfolio, User, 
	PaginatedResponse 
} from '$lib/types';