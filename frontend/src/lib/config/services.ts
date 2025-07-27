/**
 * Service URL Configuration
 * 
 * This configuration allows switching between gateway and direct service connections.
 * Set USE_GATEWAY=false to connect directly to services (temporary workaround)
 */

const USE_GATEWAY = import.meta.env.VITE_USE_GATEWAY !== 'false';

// Production service URLs
const PRODUCTION_SERVICES = {
  gateway: 'https://tradesense-gateway-production.up.railway.app',
  auth: 'https://tradesense-auth-production.up.railway.app',
  trading: 'https://tradesense-trading-production.up.railway.app',
  analytics: 'https://tradesense-analytics-production.up.railway.app',
  marketData: 'https://tradesense-market-data-production.up.railway.app',
  billing: 'https://tradesense-billing-production.up.railway.app',
  ai: 'https://tradesense-ai-production.up.railway.app'
};

// Development service URLs
const DEVELOPMENT_SERVICES = {
  gateway: 'http://localhost:8000',
  auth: 'http://localhost:8001',
  trading: 'http://localhost:8002',
  analytics: 'http://localhost:8003',
  marketData: 'http://localhost:8004',
  billing: 'http://localhost:8005',
  ai: 'http://localhost:8006'
};

// Determine if we're in production
const IS_PRODUCTION = import.meta.env.PROD || window.location.hostname !== 'localhost';

// Select appropriate service URLs
const SERVICE_URLS = IS_PRODUCTION ? PRODUCTION_SERVICES : DEVELOPMENT_SERVICES;

/**
 * Get the base URL for API requests
 * When USE_GATEWAY is true, all requests go through the gateway
 * When false, requests go directly to individual services
 */
export function getApiBaseUrl(): string {
  // Allow override via environment variable
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // Use gateway if enabled
  if (USE_GATEWAY) {
    return SERVICE_URLS.gateway;
  }
  
  // For direct service access, return empty (will be handled by getServiceUrl)
  return '';
}

/**
 * Get the URL for a specific service
 * Used when bypassing the gateway
 */
export function getServiceUrl(service: keyof typeof SERVICE_URLS): string {
  // Check for service-specific environment variable override
  const envKey = `VITE_${service.toUpperCase()}_SERVICE_URL`;
  const envValue = import.meta.env[envKey];
  if (envValue) {
    return envValue;
  }
  
  return SERVICE_URLS[service];
}

/**
 * Build a complete API endpoint URL
 * Handles both gateway and direct service routing
 */
export function buildApiUrl(endpoint: string): string {
  // Ensure endpoint starts with /
  if (!endpoint.startsWith('/')) {
    endpoint = '/' + endpoint;
  }
  
  // If using gateway, prepend the gateway URL
  if (USE_GATEWAY) {
    return `${getApiBaseUrl()}${endpoint}`;
  }
  
  // For direct service access, determine which service to use
  const service = getServiceFromEndpoint(endpoint);
  if (service) {
    return `${getServiceUrl(service)}${endpoint}`;
  }
  
  // Fallback to gateway if service cannot be determined
  return `${SERVICE_URLS.gateway}${endpoint}`;
}

/**
 * Determine which service handles a given endpoint
 */
function getServiceFromEndpoint(endpoint: string): keyof typeof SERVICE_URLS | null {
  // Remove leading slash and get first segment
  const path = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  const firstSegment = path.split('/')[0];
  
  // Map endpoints to services
  const endpointMap: Record<string, keyof typeof SERVICE_URLS> = {
    'auth': 'auth',
    'trades': 'trading',
    'trading': 'trading',
    'portfolio': 'trading',
    'journal': 'trading',
    'analytics': 'analytics',
    'patterns': 'analytics',
    'performance': 'analytics',
    'market-data': 'marketData',
    'quotes': 'marketData',
    'billing': 'billing',
    'subscriptions': 'billing',
    'ai': 'ai',
    'intelligence': 'ai',
    'insights': 'ai'
  };
  
  return endpointMap[firstSegment] || null;
}

// Export configuration status
export const serviceConfig = {
  usingGateway: USE_GATEWAY,
  isProduction: IS_PRODUCTION,
  urls: SERVICE_URLS
};