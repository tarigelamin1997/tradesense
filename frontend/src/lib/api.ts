
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://your-replit-app.replit.app/api'
  : 'http://localhost:8000/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
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
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth methods
  async login(username: string, password: string) {
    const response = await this.client.post('/auth/login', {
      username,
      password,
    });
    
    if (response.data.token) {
      localStorage.setItem('auth_token', response.data.token);
    }
    
    return response.data;
  }

  async register(username: string, email: string, password: string) {
    const response = await this.client.post('/auth/register', {
      username,
      email,
      password,
    });
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // Data methods
  async uploadData(formData: FormData, config?: AxiosRequestConfig) {
    const response = await this.client.post('/data/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      ...config,
    });
    return response.data;
  }

  async analyzeData(data: any[], analysisType: string = 'comprehensive') {
    const response = await this.client.post('/analytics/analyze', {
      data,
      analysis_type: analysisType,
    });
    return response.data;
  }

  async getDashboardData(userId: string) {
    const response = await this.client.get(`/analytics/dashboard/${userId}`);
    return response.data;
  }

  async getSymbols() {
    const response = await this.client.get('/analytics/symbols');
    return response.data;
  }

  async getAvailableMetrics() {
    const response = await this.client.get('/analytics/metrics');
    return response.data;
  }

  // Generic HTTP methods
  async get(url: string, config?: AxiosRequestConfig) {
    const response = await this.client.get(url, config);
    return response;
  }

  async post(url: string, data?: any, config?: AxiosRequestConfig) {
    const response = await this.client.post(url, data, config);
    return response;
  }

  async put(url: string, data?: any, config?: AxiosRequestConfig) {
    const response = await this.client.put(url, data, config);
    return response;
  }

  async delete(url: string, config?: AxiosRequestConfig) {
    const response = await this.client.delete(url, config);
    return response;
  }

  // Utility methods
  setAuthToken(token: string) {
    localStorage.setItem('auth_token', token);
  }

  clearAuthToken() {
    localStorage.removeItem('auth_token');
  }

  getAuthToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  isAuthenticated(): boolean {
    return !!this.getAuthToken();
  }
}

export const api = new ApiClient();
export default api;
