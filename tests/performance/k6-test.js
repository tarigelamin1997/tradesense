/**
 * K6 Performance Test Suite for TradeSense
 * 
 * Comprehensive load testing with multiple scenarios
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';
import { randomString, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const errorRate = new Rate('errors');
const loginDuration = new Trend('login_duration');
const tradeDuration = new Trend('trade_creation_duration');
const analyticsDuration = new Trend('analytics_duration');
const tradeCounter = new Counter('trades_created');
const activeUsers = new Gauge('active_users');

// Test configuration
export const options = {
  scenarios: {
    // Smoke test
    smoke: {
      executor: 'constant-vus',
      vus: 1,
      duration: '1m',
      startTime: '0s',
      tags: { scenario: 'smoke' },
    },
    
    // Load test - gradual ramp up
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 10 },   // Warm up
        { duration: '5m', target: 50 },   // Normal load
        { duration: '3m', target: 100 },  // Peak load
        { duration: '2m', target: 0 },    // Cool down
      ],
      startTime: '2m',
      tags: { scenario: 'load' },
    },
    
    // Stress test
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 100 },
        { duration: '5m', target: 200 },
        { duration: '2m', target: 300 },
        { duration: '5m', target: 300 },
        { duration: '2m', target: 0 },
      ],
      startTime: '15m',
      tags: { scenario: 'stress' },
    },
    
    // Spike test
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 50 },
        { duration: '30s', target: 500 },  // Sudden spike
        { duration: '30s', target: 50 },
        { duration: '30s', target: 0 },
      ],
      startTime: '32m',
      tags: { scenario: 'spike' },
    },
    
    // Soak test (endurance)
    soak: {
      executor: 'constant-vus',
      vus: 50,
      duration: '30m',
      startTime: '35m',
      tags: { scenario: 'soak' },
    },
  },
  
  thresholds: {
    // General thresholds
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.1'],
    errors: ['rate<0.1'],
    
    // Specific endpoint thresholds
    'http_req_duration{endpoint:login}': ['p(95)<300'],
    'http_req_duration{endpoint:dashboard}': ['p(95)<500'],
    'http_req_duration{endpoint:analytics}': ['p(95)<1000'],
    'http_req_duration{endpoint:trades}': ['p(95)<400'],
  },
};

// Test data
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TEST_USERS = [];

// Generate test users
for (let i = 0; i < 100; i++) {
  TEST_USERS.push({
    email: `testuser${i}@example.com`,
    password: 'testpassword123',
  });
}

// Helper functions
function randomUser() {
  return TEST_USERS[randomIntBetween(0, TEST_USERS.length - 1)];
}

function login(user) {
  const res = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({
      email: user.email,
      password: user.password,
    }),
    {
      headers: { 'Content-Type': 'application/json' },
      tags: { endpoint: 'login' },
    }
  );
  
  const success = check(res, {
    'login successful': (r) => r.status === 200,
    'has access token': (r) => r.json('access_token') !== undefined,
  });
  
  if (!success) {
    errorRate.add(1);
  } else {
    errorRate.add(0);
  }
  
  loginDuration.add(res.timings.duration);
  
  return success ? res.json() : null;
}

function createTrade(token) {
  const symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA'];
  const trade = {
    symbol: symbols[randomIntBetween(0, symbols.length - 1)],
    trade_type: Math.random() > 0.5 ? 'BUY' : 'SELL',
    quantity: randomIntBetween(1, 100),
    entry_price: randomIntBetween(100, 500) + Math.random(),
    exit_price: randomIntBetween(100, 500) + Math.random(),
    entry_date: new Date().toISOString(),
    exit_date: new Date().toISOString(),
  };
  
  const res = http.post(
    `${BASE_URL}/api/v1/trades`,
    JSON.stringify(trade),
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      tags: { endpoint: 'trades' },
    }
  );
  
  const success = check(res, {
    'trade created': (r) => r.status === 200 || r.status === 201,
  });
  
  if (success) {
    tradeCounter.add(1);
  }
  
  tradeDuration.add(res.timings.duration);
  
  return success;
}

function viewAnalytics(token) {
  const endpoints = [
    '/api/v1/analytics/dashboard',
    '/api/v1/analytics/performance',
    '/api/v1/analytics/win-rate',
    '/api/v1/analytics/streaks',
  ];
  
  const endpoint = endpoints[randomIntBetween(0, endpoints.length - 1)];
  
  const res = http.get(
    `${BASE_URL}${endpoint}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      tags: { endpoint: 'analytics' },
    }
  );
  
  check(res, {
    'analytics loaded': (r) => r.status === 200,
  });
  
  analyticsDuration.add(res.timings.duration);
}

// Main test scenario
export default function () {
  // Track active users
  activeUsers.add(__VU);
  
  // User login
  const user = randomUser();
  const loginData = login(user);
  
  if (!loginData) {
    console.error('Login failed, skipping user actions');
    sleep(1);
    return;
  }
  
  const token = loginData.access_token;
  
  // User workflow
  group('User Actions', () => {
    // View dashboard
    group('Dashboard', () => {
      const res = http.get(
        `${BASE_URL}/api/v1/analytics/dashboard`,
        {
          headers: { 'Authorization': `Bearer ${token}` },
          tags: { endpoint: 'dashboard' },
        }
      );
      
      check(res, {
        'dashboard loaded': (r) => r.status === 200,
      });
    });
    
    sleep(randomIntBetween(1, 3));
    
    // Create trades
    group('Trade Creation', () => {
      const numTrades = randomIntBetween(1, 5);
      for (let i = 0; i < numTrades; i++) {
        createTrade(token);
        sleep(randomIntBetween(0.5, 2));
      }
    });
    
    sleep(randomIntBetween(1, 3));
    
    // View analytics
    group('Analytics', () => {
      const numViews = randomIntBetween(2, 5);
      for (let i = 0; i < numViews; i++) {
        viewAnalytics(token);
        sleep(randomIntBetween(1, 3));
      }
    });
    
    // Search trades
    group('Search', () => {
      const res = http.get(
        `${BASE_URL}/api/v1/trades?limit=50`,
        {
          headers: { 'Authorization': `Bearer ${token}` },
          tags: { endpoint: 'search' },
        }
      );
      
      check(res, {
        'search successful': (r) => r.status === 200,
      });
    });
  });
  
  // Think time
  sleep(randomIntBetween(3, 10));
}

// Setup function - runs once per VU
export function setup() {
  console.log('Setting up test data...');
  
  // Create test users if needed
  const adminToken = 'admin_token'; // Would be obtained through proper auth
  
  TEST_USERS.forEach((user, index) => {
    const res = http.post(
      `${BASE_URL}/api/v1/auth/register`,
      JSON.stringify({
        email: user.email,
        password: user.password,
        full_name: `Test User ${index}`,
      }),
      {
        headers: { 'Content-Type': 'application/json' },
      }
    );
    
    if (res.status === 201) {
      console.log(`Created user: ${user.email}`);
    }
  });
  
  return { startTime: new Date() };
}

// Teardown function - runs once at the end
export function teardown(data) {
  console.log('Test completed');
  console.log(`Duration: ${new Date() - data.startTime}ms`);
}

// Custom summary
export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'summary.json': JSON.stringify(data),
    'summary.html': htmlReport(data),
  };
}