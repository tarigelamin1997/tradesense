// API Configuration
export const API_CONFIG = {
  // Use environment variables with fallbacks
  API_URL: import.meta.env.PUBLIC_API_URL || 'https://tradesense-gateway-production.up.railway.app',
  WS_URL: import.meta.env.PUBLIC_WS_URL || 'wss://tradesense-gateway-production.up.railway.app',
  
  // API endpoints
  endpoints: {
    auth: {
      login: '/api/v1/auth/login',
      register: '/api/v1/auth/register',
      refresh: '/api/v1/auth/refresh',
      logout: '/api/v1/auth/logout',
      verify: '/api/v1/auth/verify-email',
      forgotPassword: '/api/v1/auth/forgot-password',
      resetPassword: '/api/v1/auth/reset-password'
    },
    trades: {
      list: '/api/v1/trades',
      create: '/api/v1/trades',
      update: '/api/v1/trades',
      delete: '/api/v1/trades',
      upload: '/api/v1/trades/upload'
    },
    analytics: {
      overview: '/api/v1/analytics/overview',
      performance: '/api/v1/analytics/performance',
      patterns: '/api/v1/analytics/patterns'
    }
  }
};