
import axios, { AxiosResponse } from 'axios';
import { ApiResponse, AuthResponse, LoginRequest, RegisterRequest, DashboardMetrics, Trade } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (credentials: LoginRequest): Promise<AxiosResponse<AuthResponse>> =>
    apiClient.post('/api/auth/login', credentials),
  
  register: (userData: RegisterRequest): Promise<AxiosResponse<ApiResponse<{ message: string }>>> =>
    apiClient.post('/api/auth/register', userData),
  
  getMe: (): Promise<AxiosResponse<ApiResponse<any>>> =>
    apiClient.get('/api/auth/me'),
};

export const dataApi = {
  uploadTradeData: (file: File): Promise<AxiosResponse<ApiResponse<any>>> => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/api/data/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  analyzeData: (data: any): Promise<AxiosResponse<ApiResponse<any>>> =>
    apiClient.post('/api/analytics/analyze', { data }),
  
  getDashboardData: (userId: string): Promise<AxiosResponse<DashboardMetrics>> =>
    apiClient.get(`/api/analytics/dashboard/${userId}`),
};

export default apiClient;
