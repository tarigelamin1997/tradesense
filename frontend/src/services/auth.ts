
import { apiClient } from './api';
import { User } from '../types';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

class AuthService {
  private tokenKey = 'authToken';
  private userKey = 'currentUser';

  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/api/auth/login', credentials);
    const tokenData = response.data;
    
    // Store token and user data
    localStorage.setItem(this.tokenKey, tokenData.access_token);
    localStorage.setItem(this.userKey, JSON.stringify(tokenData.user));
    
    return tokenData;
  }

  async register(userData: RegisterRequest): Promise<ApiResponse> {
    const response = await apiClient.post<ApiResponse>('/api/auth/register', userData);
    return response.data;
  }

  async refreshToken(): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/api/auth/refresh');
    const tokenData = response.data;
    
    // Update stored token and user data
    localStorage.setItem(this.tokenKey, tokenData.access_token);
    localStorage.setItem(this.userKey, JSON.stringify(tokenData.user));
    
    return tokenData;
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post('/api/auth/logout');
    } catch (error) {
      console.warn('Logout API call failed:', error);
    } finally {
      // Always clear local storage
      localStorage.removeItem(this.tokenKey);
      localStorage.removeItem(this.userKey);
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/auth/me');
    return response.data;
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  getCurrentUserFromStorage(): User | null {
    const userData = localStorage.getItem(this.userKey);
    return userData ? JSON.parse(userData) : null;
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  // Auto-refresh token when it's about to expire
  async checkAndRefreshToken(): Promise<boolean> {
    const token = this.getToken();
    if (!token) return false;

    try {
      // Try to get current user to check if token is still valid
      await this.getCurrentUser();
      return true;
    } catch (error: any) {
      if (error.response?.status === 401) {
        try {
          await this.refreshToken();
          return true;
        } catch (refreshError) {
          this.logout();
          return false;
        }
      }
      return false;
    }
  }
}

export const authService = new AuthService();
