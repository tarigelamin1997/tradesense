import { describe, it, expect } from 'vitest';
import {
  validateEmail,
  validatePassword,
  sanitizeHtml,
  escapeSql,
  validateUrl,
  validatePhone,
  validateTrade,
  validateFileUpload,
  debounce,
  rateLimit
} from '$lib/utils/validation';

describe('Validation Utilities', () => {
  describe('validateEmail', () => {
    it('should validate correct email addresses', () => {
      expect(validateEmail('test@example.com')).toBe(true);
      expect(validateEmail('user.name@company.org')).toBe(true);
      expect(validateEmail('user+tag@example.co.uk')).toBe(true);
    });

    it('should reject invalid email addresses', () => {
      expect(validateEmail('notanemail')).toBe(false);
      expect(validateEmail('@example.com')).toBe(false);
      expect(validateEmail('test@')).toBe(false);
      expect(validateEmail('test @example.com')).toBe(false);
      expect(validateEmail('')).toBe(false);
    });
  });

  describe('validatePassword', () => {
    it('should validate strong passwords', () => {
      const result = validatePassword('StrongP@ssw0rd');
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject weak passwords', () => {
      const shortPassword = validatePassword('Abc@1');
      expect(shortPassword.isValid).toBe(false);
      expect(shortPassword.errors).toContain('Password must be at least 8 characters long');

      const noUppercase = validatePassword('password@123');
      expect(noUppercase.isValid).toBe(false);
      expect(noUppercase.errors).toContain('Password must contain at least one uppercase letter');

      const noLowercase = validatePassword('PASSWORD@123');
      expect(noLowercase.isValid).toBe(false);
      expect(noLowercase.errors).toContain('Password must contain at least one lowercase letter');

      const noNumber = validatePassword('Password@abc');
      expect(noNumber.isValid).toBe(false);
      expect(noNumber.errors).toContain('Password must contain at least one number');

      const noSpecial = validatePassword('Password123');
      expect(noSpecial.isValid).toBe(false);
      expect(noSpecial.errors).toContain('Password must contain at least one special character');
    });
  });

  describe('sanitizeHtml', () => {
    it('should escape HTML entities', () => {
      expect(sanitizeHtml('<script>alert("XSS")</script>'))
        .toBe('&lt;script&gt;alert("XSS")&lt;/script&gt;');
      
      expect(sanitizeHtml('Test & <b>bold</b>'))
        .toBe('Test &amp; &lt;b&gt;bold&lt;/b&gt;');
      
      expect(sanitizeHtml('"quoted" text'))
        .toBe('&quot;quoted&quot; text');
    });

    it('should handle empty and null inputs', () => {
      expect(sanitizeHtml('')).toBe('');
      expect(sanitizeHtml(null as any)).toBe('');
      expect(sanitizeHtml(undefined as any)).toBe('');
    });
  });

  describe('escapeSql', () => {
    it('should escape SQL special characters', () => {
      expect(escapeSql("O'Brien")).toBe("O''Brien");
      expect(escapeSql('Test"Quote')).toBe('Test""Quote');
      expect(escapeSql('Line1\nLine2')).toBe('Line1\\nLine2');
      expect(escapeSql('Tab\tCharacter')).toBe('Tab\\tCharacter');
    });

    it('should handle backslashes', () => {
      expect(escapeSql('Path\\to\\file')).toBe('Path\\\\to\\\\file');
    });
  });

  describe('validateUrl', () => {
    it('should validate correct URLs', () => {
      expect(validateUrl('https://example.com')).toBe(true);
      expect(validateUrl('http://localhost:3000')).toBe(true);
      expect(validateUrl('https://sub.domain.com/path?query=1')).toBe(true);
      expect(validateUrl('ftp://files.example.com')).toBe(true);
    });

    it('should reject invalid URLs', () => {
      expect(validateUrl('not a url')).toBe(false);
      expect(validateUrl('http://')).toBe(false);
      expect(validateUrl('example.com')).toBe(false);
      expect(validateUrl('')).toBe(false);
    });
  });

  describe('validatePhone', () => {
    it('should validate correct phone numbers', () => {
      expect(validatePhone('+1234567890')).toBe(true);
      expect(validatePhone('+44 20 7123 4567')).toBe(true);
      expect(validatePhone('+1-800-555-0123')).toBe(true);
    });

    it('should reject invalid phone numbers', () => {
      expect(validatePhone('123')).toBe(false);
      expect(validatePhone('not a phone')).toBe(false);
      expect(validatePhone('+1')).toBe(false);
      expect(validatePhone('')).toBe(false);
    });
  });

  describe('validateTrade', () => {
    it('should validate correct trade data', () => {
      const validTrade = {
        symbol: 'AAPL',
        quantity: 100,
        price: 150.50,
        type: 'buy' as const
      };

      const result = validateTrade(validTrade);
      expect(result.isValid).toBe(true);
      expect(result.errors).toEqual({});
    });

    it('should reject invalid trade data', () => {
      const invalidTrade = {
        symbol: '',
        quantity: -10,
        price: 0,
        type: 'invalid' as any
      };

      const result = validateTrade(invalidTrade);
      expect(result.isValid).toBe(false);
      expect(result.errors.symbol).toBe('Symbol is required');
      expect(result.errors.quantity).toBe('Quantity must be positive');
      expect(result.errors.price).toBe('Price must be positive');
      expect(result.errors.type).toBe('Invalid trade type');
    });

    it('should validate symbol length', () => {
      const longSymbol = {
        symbol: 'VERYLONGSYMBOL',
        quantity: 100,
        price: 50,
        type: 'sell' as const
      };

      const result = validateTrade(longSymbol);
      expect(result.isValid).toBe(false);
      expect(result.errors.symbol).toBe('Symbol must be 1-10 characters');
    });
  });

  describe('validateFileUpload', () => {
    it('should validate allowed file types', () => {
      const imageFile = new File([''], 'test.jpg', { type: 'image/jpeg' });
      const imageResult = validateFileUpload(imageFile, {
        allowedTypes: ['image/jpeg', 'image/png'],
        maxSize: 5 * 1024 * 1024
      });
      expect(imageResult.isValid).toBe(true);
    });

    it('should reject disallowed file types', () => {
      const exeFile = new File([''], 'malware.exe', { type: 'application/x-msdownload' });
      const result = validateFileUpload(exeFile, {
        allowedTypes: ['image/jpeg', 'image/png'],
        maxSize: 5 * 1024 * 1024
      });
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('File type not allowed');
    });

    it('should reject files exceeding size limit', () => {
      const largeFile = new File(['x'.repeat(10 * 1024 * 1024)], 'large.jpg', { type: 'image/jpeg' });
      Object.defineProperty(largeFile, 'size', { value: 10 * 1024 * 1024 });
      
      const result = validateFileUpload(largeFile, {
        allowedTypes: ['image/jpeg'],
        maxSize: 5 * 1024 * 1024
      });
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('File size exceeds limit (5.00 MB)');
    });
  });

  describe('debounce', () => {
    it('should debounce function calls', async () => {
      let callCount = 0;
      const fn = () => callCount++;
      const debouncedFn = debounce(fn, 100);

      // Call multiple times rapidly
      debouncedFn();
      debouncedFn();
      debouncedFn();

      // Should not have been called yet
      expect(callCount).toBe(0);

      // Wait for debounce delay
      await new Promise(resolve => setTimeout(resolve, 150));

      // Should have been called once
      expect(callCount).toBe(1);
    });

    it('should cancel previous timeouts', async () => {
      let callCount = 0;
      const fn = () => callCount++;
      const debouncedFn = debounce(fn, 100);

      // First call
      debouncedFn();
      
      // Wait 50ms (less than debounce delay)
      await new Promise(resolve => setTimeout(resolve, 50));
      
      // Second call should cancel first
      debouncedFn();
      
      // Wait another 150ms
      await new Promise(resolve => setTimeout(resolve, 150));
      
      // Should only have been called once
      expect(callCount).toBe(1);
    });
  });

  describe('rateLimit', () => {
    it('should limit function calls', async () => {
      let callCount = 0;
      const fn = () => {
        callCount++;
        return callCount;
      };
      const limitedFn = rateLimit(fn, 2, 1000);

      // First two calls should succeed
      expect(limitedFn()).toBe(1);
      expect(limitedFn()).toBe(2);

      // Third call should fail
      expect(() => limitedFn()).toThrow('Rate limit exceeded');

      // Should still be limited
      expect(callCount).toBe(2);
    });

    it('should reset after time window', async () => {
      let callCount = 0;
      const fn = () => ++callCount;
      const limitedFn = rateLimit(fn, 1, 100);

      // First call succeeds
      expect(limitedFn()).toBe(1);

      // Second call fails
      expect(() => limitedFn()).toThrow('Rate limit exceeded');

      // Wait for window to reset
      await new Promise(resolve => setTimeout(resolve, 150));

      // Should work again
      expect(limitedFn()).toBe(2);
    });
  });
});