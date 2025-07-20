import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import type { AxiosError } from 'axios';

export interface ApiError {
	message: string;
	status: number;
	detail?: any;
}

class SSRSafeApiClient {
	private static instance: SSRSafeApiClient | null = null;
	private axiosInstance: any = null;
	private initialized = false;

	private constructor() {}

	static getInstance(): SSRSafeApiClient {
		if (!SSRSafeApiClient.instance) {
			SSRSafeApiClient.instance = new SSRSafeApiClient();
		}
		return SSRSafeApiClient.instance;
	}

	private async initializeClient() {
		if (this.initialized || !browser) return;

		try {
			const { default: axios } = await import('axios');
			
			this.axiosInstance = axios.create({
				baseURL: import.meta.env.VITE_API_URL || '',
				timeout: 30000,
				headers: {
					'Content-Type': 'application/json',
				},
			});

			// Load token from localStorage
			const token = this.getStoredToken();
			if (token) {
				this.axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
			}

			// Setup interceptors
			this.setupInterceptors();
			this.initialized = true;
		} catch (error) {
			console.error('Failed to initialize API client:', error);
		}
	}

	private setupInterceptors() {
		if (!this.axiosInstance) return;

		// Response interceptor for error handling
		this.axiosInstance.interceptors.response.use(
			(response: any) => response,
			async (error: AxiosError) => {
				if (error.response?.status === 401) {
					this.clearStoredToken();
					if (browser) {
						await goto('/login');
					}
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
	}

	private getStoredToken(): string | null {
		if (!browser) return null;
		try {
			return localStorage.getItem('authToken');
		} catch {
			return null;
		}
	}

	private clearStoredToken(): void {
		if (!browser) return;
		try {
			localStorage.removeItem('authToken');
		} catch {
			// Ignore localStorage errors
		}
	}

	// Public API methods
	async get<T = any>(url: string, params?: any): Promise<T> {
		if (!browser) {
			// Return empty data during SSR
			return {} as T;
		}
		await this.initializeClient();
		if (!this.axiosInstance) throw new Error('API client not initialized');
		const response = await this.axiosInstance.get<T>(url, { params });
		return response.data;
	}

	async post<T = any>(url: string, data?: any, config?: any): Promise<T> {
		if (!browser) {
			// Return empty data during SSR
			return {} as T;
		}
		await this.initializeClient();
		if (!this.axiosInstance) throw new Error('API client not initialized');
		const response = await this.axiosInstance.post<T>(url, data, config);
		return response.data;
	}

	async put<T = any>(url: string, data?: any): Promise<T> {
		if (!browser) {
			// Return empty data during SSR
			return {} as T;
		}
		await this.initializeClient();
		if (!this.axiosInstance) throw new Error('API client not initialized');
		const response = await this.axiosInstance.put<T>(url, data);
		return response.data;
	}

	async patch<T = any>(url: string, data?: any): Promise<T> {
		if (!browser) {
			// Return empty data during SSR
			return {} as T;
		}
		await this.initializeClient();
		if (!this.axiosInstance) throw new Error('API client not initialized');
		const response = await this.axiosInstance.patch<T>(url, data);
		return response.data;
	}

	async delete<T = any>(url: string): Promise<T> {
		if (!browser) {
			// Return empty data during SSR
			return {} as T;
		}
		await this.initializeClient();
		if (!this.axiosInstance) throw new Error('API client not initialized');
		const response = await this.axiosInstance.delete<T>(url);
		return response.data;
	}

	setAuthToken(token: string): void {
		if (!browser) return;
		try {
			localStorage.setItem('authToken', token);
			if (this.axiosInstance) {
				this.axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
			}
		} catch {
			// Ignore localStorage errors
		}
	}

	clearAuth(): void {
		if (!browser) return;
		this.clearStoredToken();
		if (this.axiosInstance) {
			delete this.axiosInstance.defaults.headers.common['Authorization'];
		}
	}

	getAuthToken(): string | null {
		return this.getStoredToken();
	}

	isAuthenticated(): boolean {
		return !!this.getStoredToken();
	}
}

// Export singleton instance
export const api = SSRSafeApiClient.getInstance();