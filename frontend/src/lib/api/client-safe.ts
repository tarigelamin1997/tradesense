import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import type { AxiosInstance, AxiosError } from 'axios';

// Environment variables
const getApiBaseUrl = () => browser ? (import.meta.env.VITE_API_URL || '') : '';

export interface ApiError {
	message: string;
	status: number;
	detail?: any;
}

// Lazy singleton pattern - nothing created at module level
let apiInstance: any = null;

async function getApiClient() {
	if (!browser) {
		// Return a mock for SSR
		return {
			get: () => Promise.reject(new Error('API not available during SSR')),
			post: () => Promise.reject(new Error('API not available during SSR')),
			put: () => Promise.reject(new Error('API not available during SSR')),
			patch: () => Promise.reject(new Error('API not available during SSR')),
			delete: () => Promise.reject(new Error('API not available during SSR'))
		};
	}

	if (!apiInstance) {
		// Dynamically import axios only when needed
		const { default: axios } = await import('axios');
		
		const client = axios.create({
			baseURL: getApiBaseUrl(),
			timeout: 30000,
			headers: {
				'Content-Type': 'application/json',
			},
		});

		// Load token
		const token = localStorage.getItem('authToken');
		if (token) {
			client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
		}

		// Request interceptor
		client.interceptors.request.use(
			(config) => {
				console.log('Making request to:', config.url);
				return config;
			},
			(error) => Promise.reject(error)
		);

		// Response interceptor
		client.interceptors.response.use(
			(response) => response,
			async (error: AxiosError) => {
				console.error('API Error:', error.message);
				
				if (error.response?.status === 401) {
					localStorage.removeItem('authToken');
					goto('/login');
				}
				
				const responseData = error.response?.data as any;
				const apiError: ApiError = {
					message: responseData?.detail || responseData?.message || error.message || 'An error occurred',
					status: error.response?.status || 500,
					detail: responseData
				};
				
				return Promise.reject(apiError);
			}
		);

		apiInstance = client;
	}

	return apiInstance;
}

// Export safe wrapper functions
export const api = {
	async get<T = any>(url: string, params?: any): Promise<T> {
		const client = await getApiClient();
		const response = await client.get<T>(url, { params });
		return response.data;
	},

	async post<T = any>(url: string, data?: any, config?: any): Promise<T> {
		const client = await getApiClient();
		const response = await client.post<T>(url, data, config);
		return response.data;
	},

	async put<T = any>(url: string, data?: any): Promise<T> {
		const client = await getApiClient();
		const response = await client.put<T>(url, data);
		return response.data;
	},

	async patch<T = any>(url: string, data?: any): Promise<T> {
		const client = await getApiClient();
		const response = await client.patch<T>(url, data);
		return response.data;
	},

	async delete<T = any>(url: string): Promise<T> {
		const client = await getApiClient();
		const response = await client.delete<T>(url);
		return response.data;
	},

	setAuthToken(token: string): void {
		if (!browser) return;
		localStorage.setItem('authToken', token);
		// Token will be applied when client is initialized
	},

	clearAuth(): void {
		if (!browser) return;
		localStorage.removeItem('authToken');
		// Auth will be cleared on next client initialization
	},

	getAuthToken(): string | null {
		if (!browser) return null;
		return localStorage.getItem('authToken');
	},

	isAuthenticated(): boolean {
		if (!browser) return false;
		return !!localStorage.getItem('authToken');
	}
};