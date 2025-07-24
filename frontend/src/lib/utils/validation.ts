import type { ValidationRule, FormField } from '$lib/types';

// XSS prevention - sanitize HTML input
export function sanitizeHtml(input: string): string {
  const div = document.createElement('div');
  div.textContent = input;
  return div.innerHTML;
}

// SQL injection prevention - escape special characters
export function escapeSql(input: string): string {
  return input
    .replace(/[\0\x08\x09\x1a\n\r"'\\\%]/g, (char) => {
      switch (char) {
        case '\0': return '\\0';
        case '\x08': return '\\b';
        case '\x09': return '\\t';
        case '\x1a': return '\\z';
        case '\n': return '\\n';
        case '\r': return '\\r';
        case '"':
        case "'":
        case '\\':
        case '%':
          return '\\' + char;
        default:
          return char;
      }
    });
}

// Validate email format
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// Validate password strength
export function validatePassword(password: string): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];
  
  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  if (!/[0-9]/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  if (!/[^A-Za-z0-9]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}

// Validate URL format
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

// Validate phone number
export function isValidPhone(phone: string): boolean {
  const phoneRegex = /^\+?[\d\s-().]+$/;
  return phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 10;
}

// Validate trading-specific inputs
export function validateTrade(trade: {
  symbol?: string;
  quantity?: number;
  price?: number;
  type?: string;
}): { isValid: boolean; errors: Record<string, string> } {
  const errors: Record<string, string> = {};
  
  if (!trade.symbol || trade.symbol.trim().length === 0) {
    errors.symbol = 'Symbol is required';
  } else if (!/^[A-Z0-9\-\.]+$/i.test(trade.symbol)) {
    errors.symbol = 'Invalid symbol format';
  }
  
  if (trade.quantity === undefined || trade.quantity === null) {
    errors.quantity = 'Quantity is required';
  } else if (trade.quantity <= 0) {
    errors.quantity = 'Quantity must be greater than 0';
  }
  
  if (trade.price === undefined || trade.price === null) {
    errors.price = 'Price is required';
  } else if (trade.price <= 0) {
    errors.price = 'Price must be greater than 0';
  }
  
  if (!trade.type || !['buy', 'sell'].includes(trade.type.toLowerCase())) {
    errors.type = 'Type must be either buy or sell';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}

// Generic form validation
export function validateForm<T extends Record<string, FormField>>(
  fields: T
): { isValid: boolean; errors: Record<keyof T, string | null> } {
  const errors: Record<keyof T, string | null> = {} as any;
  let isValid = true;
  
  for (const [fieldName, field] of Object.entries(fields)) {
    errors[fieldName as keyof T] = null;
    
    for (const rule of field.rules) {
      if (rule.required && !field.value) {
        errors[fieldName as keyof T] = rule.message;
        isValid = false;
        break;
      }
      
      if (rule.minLength && field.value?.length < rule.minLength) {
        errors[fieldName as keyof T] = rule.message;
        isValid = false;
        break;
      }
      
      if (rule.maxLength && field.value?.length > rule.maxLength) {
        errors[fieldName as keyof T] = rule.message;
        isValid = false;
        break;
      }
      
      if (rule.pattern && !rule.pattern.test(field.value)) {
        errors[fieldName as keyof T] = rule.message;
        isValid = false;
        break;
      }
      
      if (rule.custom && !rule.custom(field.value)) {
        errors[fieldName as keyof T] = rule.message;
        isValid = false;
        break;
      }
    }
  }
  
  return { isValid, errors };
}

// Rate limiting helper
export function createRateLimiter(maxRequests: number, windowMs: number) {
  const requests = new Map<string, number[]>();
  
  return function isAllowed(key: string): boolean {
    const now = Date.now();
    const windowStart = now - windowMs;
    
    // Get existing requests for this key
    const keyRequests = requests.get(key) || [];
    
    // Filter out old requests
    const recentRequests = keyRequests.filter(time => time > windowStart);
    
    // Check if limit exceeded
    if (recentRequests.length >= maxRequests) {
      return false;
    }
    
    // Add new request
    recentRequests.push(now);
    requests.set(key, recentRequests);
    
    // Clean up old entries periodically
    if (Math.random() < 0.01) {
      for (const [k, v] of requests.entries()) {
        const recent = v.filter(time => time > windowStart);
        if (recent.length === 0) {
          requests.delete(k);
        } else {
          requests.set(k, recent);
        }
      }
    }
    
    return true;
  };
}

// Debounce function for search inputs
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Safe JSON parse
export function safeJsonParse<T>(json: string, fallback: T): T {
  try {
    return JSON.parse(json);
  } catch {
    return fallback;
  }
}

// Truncate text safely
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

// Format currency safely
export function formatCurrency(
  amount: number,
  currency = 'USD',
  locale = 'en-US'
): string {
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency
    }).format(amount);
  } catch {
    return `${currency} ${amount.toFixed(2)}`;
  }
}

// Safe number parsing
export function parseNumber(value: any, fallback = 0): number {
  const parsed = Number(value);
  return isNaN(parsed) ? fallback : parsed;
}

// Validate file upload
export function validateFile(
  file: File,
  options: {
    maxSize?: number; // in bytes
    allowedTypes?: string[];
    allowedExtensions?: string[];
  }
): { isValid: boolean; error?: string } {
  const { maxSize, allowedTypes, allowedExtensions } = options;
  
  if (maxSize && file.size > maxSize) {
    return {
      isValid: false,
      error: `File size must be less than ${(maxSize / 1024 / 1024).toFixed(2)}MB`
    };
  }
  
  if (allowedTypes && !allowedTypes.includes(file.type)) {
    return {
      isValid: false,
      error: `File type must be one of: ${allowedTypes.join(', ')}`
    };
  }
  
  if (allowedExtensions) {
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!extension || !allowedExtensions.includes(extension)) {
      return {
        isValid: false,
        error: `File extension must be one of: ${allowedExtensions.join(', ')}`
      };
    }
  }
  
  return { isValid: true };
}