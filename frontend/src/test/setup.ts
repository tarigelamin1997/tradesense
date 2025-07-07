import '@testing-library/jest-dom';
import { configure } from '@testing-library/react';
import { server } from './mocks/server';

// Configure testing library
configure({ testIdAttribute: 'data-testid' });

// Mock API server
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}));

// Mock environment variables
process.env.REACT_APP_API_URL = 'http://localhost:8000';
process.env.NODE_ENV = 'test';

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  observe() {
    return null;
  }
  disconnect() {
    return null;
  }
  unobserve() {
    return null;
  }
};

// Mock PerformanceObserver
global.PerformanceObserver = class PerformanceObserver {
  constructor() {}
  observe() {
    return null;
  }
  disconnect() {
    return null;
  }
};

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock fetch
global.fetch = jest.fn();

// Mock console methods in tests to avoid noise
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

// Global test utilities
export const mockApiResponse = (data: any, status = 200) => {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  });
};

export const mockApiError = (status = 500, message = 'Server Error') => {
  return Promise.reject({
    status,
    message,
    response: {
      status,
      data: { message }
    }
  });
};

// Accessibility testing helpers
export const axeConfig = {
  rules: {
    // Disable color-contrast rule for tests as it's hard to test
    'color-contrast': { enabled: false },
  },
};

// Custom matchers for accessibility
expect.extend({
  toBeAccessible: async (received) => {
    const { axe } = await import('jest-axe');
    const results = await axe(received, axeConfig);

    if (results.violations.length === 0) {
      return {
        pass: true,
        message: () => 'Expected element to have accessibility violations, but none were found',
      };
    }

    return {
      pass: false,
      message: () => {
        const violations = results.violations
          .map(violation => `${violation.id}: ${violation.description}`)
          .join('\n');
        return `Expected element to be accessible, but found violations:\n${violations}`;
      },
    };
  },
});