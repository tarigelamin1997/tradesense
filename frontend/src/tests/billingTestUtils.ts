import { User } from '../types/user';
import { SubscriptionTier, BillingStatus } from '../types/billing';

// Stripe test card numbers and their expected behaviors
export const STRIPE_TEST_CARDS = {
  // Successful payment cards
  SUCCESS: {
    number: '4242424242424242',
    description: 'Succeeds with any CVC and future expiry',
    expectedBehavior: 'Payment succeeds'
  },
  SUCCESS_3D_SECURE: {
    number: '4000002500003155',
    description: 'Requires 3D Secure authentication',
    expectedBehavior: 'Opens 3D Secure modal, then succeeds'
  },
  
  // Failure cards
  DECLINED: {
    number: '4000000000000002',
    description: 'Always declines',
    expectedBehavior: 'Payment fails with card_declined'
  },
  INSUFFICIENT_FUNDS: {
    number: '4000000000009995',
    description: 'Declines with insufficient funds',
    expectedBehavior: 'Payment fails with insufficient_funds'
  },
  EXPIRED_CARD: {
    number: '4000000000000069',
    description: 'Declines as expired card',
    expectedBehavior: 'Payment fails with expired_card'
  },
  INCORRECT_CVC: {
    number: '4000000000000127',
    description: 'Declines with incorrect CVC',
    expectedBehavior: 'Payment fails with incorrect_cvc'
  },
  PROCESSING_ERROR: {
    number: '4000000000000119',
    description: 'Declines with processing error',
    expectedBehavior: 'Payment fails with processing_error'
  },
  
  // Special behavior cards
  ATTACH_FAILS: {
    number: '4000000000000341',
    description: 'Attaching to customer fails',
    expectedBehavior: 'Card validation succeeds but customer attachment fails'
  },
  CHARGE_CUSTOMER_FAIL: {
    number: '4000000000002685',
    description: 'Charging customer fails after attach',
    expectedBehavior: 'Card attaches but charge fails'
  }
};

// User state generators
export const generateUser = (overrides: Partial<User> = {}): User => ({
  id: 'test-user-123',
  email: 'test@example.com',
  name: 'Test User',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides
});

export const generateFreeUser = (): User => generateUser({
  subscription_tier: SubscriptionTier.FREE,
  billing_status: BillingStatus.ACTIVE,
  stripe_customer_id: null,
  stripe_subscription_id: null,
  trial_ends_at: null
});

export const generateTrialUser = (daysRemaining: number = 7): User => {
  const trialEndDate = new Date();
  trialEndDate.setDate(trialEndDate.getDate() + daysRemaining);
  
  return generateUser({
    subscription_tier: SubscriptionTier.TRIAL,
    billing_status: BillingStatus.TRIALING,
    stripe_customer_id: 'cus_trial_' + Date.now(),
    stripe_subscription_id: null,
    trial_ends_at: trialEndDate.toISOString()
  });
};

export const generateExpiredTrialUser = (): User => {
  const expiredDate = new Date();
  expiredDate.setDate(expiredDate.getDate() - 1);
  
  return generateUser({
    subscription_tier: SubscriptionTier.FREE,
    billing_status: BillingStatus.ACTIVE,
    stripe_customer_id: 'cus_expired_trial_' + Date.now(),
    stripe_subscription_id: null,
    trial_ends_at: expiredDate.toISOString()
  });
};

export const generatePaidUser = (tier: SubscriptionTier.PRO | SubscriptionTier.ENTERPRISE = SubscriptionTier.PRO): User => generateUser({
  subscription_tier: tier,
  billing_status: BillingStatus.ACTIVE,
  stripe_customer_id: 'cus_paid_' + Date.now(),
  stripe_subscription_id: 'sub_paid_' + Date.now(),
  trial_ends_at: null
});

export const generatePastDueUser = (): User => generateUser({
  subscription_tier: SubscriptionTier.PRO,
  billing_status: BillingStatus.PAST_DUE,
  stripe_customer_id: 'cus_past_due_' + Date.now(),
  stripe_subscription_id: 'sub_past_due_' + Date.now(),
  trial_ends_at: null
});

export const generateCanceledUser = (): User => generateUser({
  subscription_tier: SubscriptionTier.FREE,
  billing_status: BillingStatus.CANCELED,
  stripe_customer_id: 'cus_canceled_' + Date.now(),
  stripe_subscription_id: null,
  trial_ends_at: null
});

// Mock API responses
export const mockBillingResponses = {
  checkoutSession: {
    success: {
      session_id: 'cs_test_success_123',
      url: 'https://checkout.stripe.com/pay/cs_test_success_123'
    },
    insufficientPermissions: {
      error: 'Insufficient permissions',
      code: 403
    },
    serverError: {
      error: 'Internal server error',
      code: 500
    }
  },
  
  billingPortal: {
    success: {
      url: 'https://billing.stripe.com/session/test_portal_123'
    },
    noSubscription: {
      error: 'No active subscription found',
      code: 404
    },
    unauthorized: {
      error: 'Unauthorized',
      code: 401
    }
  },
  
  subscription: {
    active: {
      id: 'sub_123',
      status: 'active',
      current_period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      cancel_at_period_end: false,
      items: [{
        price: {
          id: 'price_pro_monthly',
          product: 'prod_pro',
          unit_amount: 2900,
          currency: 'usd',
          recurring: {
            interval: 'month',
            interval_count: 1
          }
        }
      }]
    },
    
    trialing: {
      id: 'sub_trial_123',
      status: 'trialing',
      trial_end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      current_period_end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      cancel_at_period_end: false
    },
    
    pastDue: {
      id: 'sub_past_due_123',
      status: 'past_due',
      current_period_end: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      cancel_at_period_end: false
    },
    
    canceled: {
      id: 'sub_canceled_123',
      status: 'canceled',
      canceled_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      current_period_end: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      cancel_at_period_end: true
    }
  },
  
  webhooks: {
    checkoutComplete: {
      type: 'checkout.session.completed',
      data: {
        object: {
          id: 'cs_test_123',
          customer: 'cus_123',
          subscription: 'sub_123',
          payment_status: 'paid'
        }
      }
    },
    
    paymentFailed: {
      type: 'invoice.payment_failed',
      data: {
        object: {
          id: 'in_123',
          customer: 'cus_123',
          subscription: 'sub_123',
          attempt_count: 1,
          next_payment_attempt: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString()
        }
      }
    },
    
    subscriptionDeleted: {
      type: 'customer.subscription.deleted',
      data: {
        object: {
          id: 'sub_123',
          customer: 'cus_123',
          status: 'canceled',
          canceled_at: Date.now() / 1000
        }
      }
    }
  }
};

// Test scenario generators
export const testScenarios = {
  // Free to paid upgrade scenarios
  freeUserUpgrade: {
    initial: generateFreeUser(),
    action: 'User clicks upgrade button',
    expected: 'Redirect to Stripe checkout',
    mockResponse: mockBillingResponses.checkoutSession.success
  },
  
  // Trial expiration scenarios
  trialAboutToExpire: {
    initial: generateTrialUser(3),
    action: 'User logs in with 3 days left',
    expected: 'Show trial expiration warning',
    mockResponse: null
  },
  
  trialExpired: {
    initial: generateExpiredTrialUser(),
    action: 'User attempts to access paid feature',
    expected: 'Show upgrade prompt',
    mockResponse: null
  },
  
  // Payment failure scenarios
  cardDeclined: {
    initial: generatePaidUser(),
    action: 'Monthly charge fails',
    expected: 'User status changes to past_due',
    mockResponse: mockBillingResponses.webhooks.paymentFailed
  },
  
  // Cancellation scenarios
  voluntaryCancellation: {
    initial: generatePaidUser(),
    action: 'User cancels subscription',
    expected: 'Access until period end, then downgrade',
    mockResponse: mockBillingResponses.subscription.canceled
  },
  
  // Edge cases
  multipleFailedPayments: {
    initial: generatePastDueUser(),
    action: 'Third payment attempt fails',
    expected: 'Subscription canceled, user downgraded',
    mockResponse: mockBillingResponses.webhooks.subscriptionDeleted
  },
  
  concurrentUpgrades: {
    initial: generateFreeUser(),
    action: 'User opens checkout in multiple tabs',
    expected: 'Only one checkout session succeeds',
    mockResponse: mockBillingResponses.checkoutSession.success
  },
  
  downgradeDuringTrial: {
    initial: generateTrialUser(14),
    action: 'User attempts to downgrade',
    expected: 'Trial continues, downgrade scheduled',
    mockResponse: null
  }
};

// Helper functions
export const simulateBillingState = (state: BillingStatus): Partial<User> => {
  switch (state) {
    case BillingStatus.ACTIVE:
      return {
        billing_status: BillingStatus.ACTIVE,
        subscription_tier: SubscriptionTier.PRO
      };
    case BillingStatus.PAST_DUE:
      return {
        billing_status: BillingStatus.PAST_DUE,
        subscription_tier: SubscriptionTier.PRO
      };
    case BillingStatus.CANCELED:
      return {
        billing_status: BillingStatus.CANCELED,
        subscription_tier: SubscriptionTier.FREE
      };
    case BillingStatus.TRIALING:
      return {
        billing_status: BillingStatus.TRIALING,
        subscription_tier: SubscriptionTier.TRIAL,
        trial_ends_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
      };
    default:
      return {
        billing_status: BillingStatus.ACTIVE,
        subscription_tier: SubscriptionTier.FREE
      };
  }
};

export const mockStripeElements = () => ({
  create: jest.fn(() => ({
    mount: jest.fn(),
    unmount: jest.fn(),
    on: jest.fn(),
    update: jest.fn(),
    destroy: jest.fn()
  })),
  getElement: jest.fn(() => ({
    focus: jest.fn(),
    blur: jest.fn(),
    clear: jest.fn()
  }))
});

export const mockStripe = () => ({
  confirmPayment: jest.fn(() => Promise.resolve({ error: null })),
  createPaymentMethod: jest.fn(() => Promise.resolve({ 
    paymentMethod: { id: 'pm_test_123' },
    error: null 
  })),
  elements: mockStripeElements,
  redirectToCheckout: jest.fn(() => Promise.resolve({ error: null }))
});

// Test data for usage limits
export const usageLimits = {
  [SubscriptionTier.FREE]: {
    trades: 50,
    journalEntries: 10,
    attachments: 0,
    advancedAnalytics: false
  },
  [SubscriptionTier.TRIAL]: {
    trades: -1, // unlimited
    journalEntries: -1,
    attachments: 10,
    advancedAnalytics: true
  },
  [SubscriptionTier.PRO]: {
    trades: -1,
    journalEntries: -1,
    attachments: -1,
    advancedAnalytics: true
  },
  [SubscriptionTier.ENTERPRISE]: {
    trades: -1,
    journalEntries: -1,
    attachments: -1,
    advancedAnalytics: true,
    apiAccess: true,
    prioritySupport: true
  }
};

// Helper to generate usage data
export const generateUsageData = (percentUsed: number, tier: SubscriptionTier) => {
  const limits = usageLimits[tier];
  return {
    trades: {
      used: Math.floor((limits.trades * percentUsed) / 100),
      limit: limits.trades
    },
    journalEntries: {
      used: Math.floor((limits.journalEntries * percentUsed) / 100),
      limit: limits.journalEntries
    },
    attachments: {
      used: Math.floor((limits.attachments * percentUsed) / 100),
      limit: limits.attachments
    }
  };
};

// Mock localStorage for testing
export const mockLocalStorage = () => {
  let store: Record<string, string> = {};
  
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => { store[key] = value; }),
    removeItem: jest.fn((key: string) => { delete store[key]; }),
    clear: jest.fn(() => { store = {}; }),
    get length() { return Object.keys(store).length; },
    key: jest.fn((index: number) => Object.keys(store)[index] || null)
  };
};

// Helper to simulate webhook events
export const simulateWebhook = (eventType: string, customData?: any) => {
  const baseEvent = {
    id: 'evt_test_' + Date.now(),
    type: eventType,
    created: Date.now() / 1000,
    livemode: false
  };
  
  switch (eventType) {
    case 'checkout.session.completed':
      return {
        ...baseEvent,
        data: customData || mockBillingResponses.webhooks.checkoutComplete.data
      };
    case 'invoice.payment_failed':
      return {
        ...baseEvent,
        data: customData || mockBillingResponses.webhooks.paymentFailed.data
      };
    case 'customer.subscription.deleted':
      return {
        ...baseEvent,
        data: customData || mockBillingResponses.webhooks.subscriptionDeleted.data
      };
    default:
      return {
        ...baseEvent,
        data: customData || { object: {} }
      };
  }
};

// Test helper for async billing operations
export const waitForBillingUpdate = async (callback: () => void, timeout = 5000) => {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const checkUpdate = () => {
      try {
        callback();
        resolve(true);
      } catch (error) {
        if (Date.now() - startTime > timeout) {
          reject(new Error('Billing update timeout'));
        } else {
          setTimeout(checkUpdate, 100);
        }
      }
    };
    
    checkUpdate();
  });
};

// Export test utilities for specific features
export const billingTestUtils = {
  cards: STRIPE_TEST_CARDS,
  users: {
    free: generateFreeUser,
    trial: generateTrialUser,
    expiredTrial: generateExpiredTrialUser,
    paid: generatePaidUser,
    pastDue: generatePastDueUser,
    canceled: generateCanceledUser
  },
  mocks: {
    responses: mockBillingResponses,
    stripe: mockStripe,
    localStorage: mockLocalStorage
  },
  scenarios: testScenarios,
  helpers: {
    simulateBillingState,
    generateUsageData,
    simulateWebhook,
    waitForBillingUpdate
  }
};