import { apiClient } from './api';
import { User } from '../types';

export interface LoginRequest {
  email?: string;
  username?: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
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
    console.log('=== AUTH DEBUG START ===');
    console.log('1. Login function called with:', credentials);
    console.log('2. About to make API call');
    
    try {
      const response = await apiClient.post<TokenResponse>('/api/v1/auth/login', credentials);
      console.log('3. API call completed');
      console.log('4. Response status:', response.status);
      console.log('5. Response data:', response.data);
      console.log('6. Response headers:', response.headers);
      
      const tokenData = response.data;
      console.log('7. tokenData:', tokenData);
      console.log('8. tokenData.user:', tokenData.user);
      console.log('9. tokenData.user_id:', (tokenData as any).user_id);
      console.log('10. tokenData.username:', (tokenData as any).username);
      console.log('11. tokenData.email:', (tokenData as any).email);
      
      // FIX: Backend doesn't return a 'user' object, it returns user data as separate fields
      // Create the user object from the response data
      const user = {
        id: (tokenData as any).user_id,
        username: (tokenData as any).username,
        email: (tokenData as any).email
      };
      
      console.log('12. Created user object:', user);
      
      // Store token and user data
      localStorage.setItem(this.tokenKey, tokenData.access_token);
      localStorage.setItem(this.userKey, JSON.stringify(user));
      
      console.log('13. Data stored in localStorage');
      
      // Return the data in the format the frontend expects
      const fixedTokenData = {
        ...tokenData,
        user: user
      };
      
      console.log('14. Returning fixed token data:', fixedTokenData);
      console.log('=== AUTH DEBUG END ===');
      
      return fixedTokenData as TokenResponse;
    } catch (error: any) {
      console.log('=== AUTH ERROR ===');
      console.log('15. ERROR CAUGHT:', error);
      console.log('16. Error type:', error.constructor.name);
      console.log('17. Error response:', error.response);
      console.log('18. Error message:', error.message);
      console.log('=== AUTH ERROR END ===');
      throw error;
    }
  }

  async register(userData: RegisterRequest): Promise<ApiResponse> {
    console.log('=== REGISTER DEBUG START ===');
    console.log('1. Register function called with:', userData);
    
    try {
      const response = await apiClient.post<ApiResponse>('/api/v1/auth/register', userData);
      console.log('2. Response status:', response.status);
      console.log('3. Response data:', response.data);
      
      // Backend returns user data directly, not wrapped in ApiResponse format
      // Fix the response to match expected format
      const fixedResponse = {
        success: true,
        data: response.data,
        message: 'Registration successful'
      };
      
      console.log('4. Fixed response:', fixedResponse);
      console.log('=== REGISTER DEBUG END ===');
      
      return fixedResponse;
    } catch (error: any) {
      console.log('=== REGISTER ERROR ===');
      console.log('5. ERROR CAUGHT:', error);
      console.log('6. Error response:', error.response);
      console.log('=== REGISTER ERROR END ===');
      throw error;
    }
  }

  async refreshToken(): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/api/v1/auth/refresh');
    const tokenData = response.data;
    
    // Update stored token and user data
    localStorage.setItem(this.tokenKey, tokenData.access_token);
    localStorage.setItem(this.userKey, JSON.stringify(tokenData.user));
    
    return tokenData;
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post('/api/v1/auth/logout');
    } catch (error) {
      console.warn('Logout API call failed:', error);
    } finally {
      // Always clear local storage
      localStorage.removeItem(this.tokenKey);
      localStorage.removeItem(this.userKey);
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/v1/auth/me');
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
