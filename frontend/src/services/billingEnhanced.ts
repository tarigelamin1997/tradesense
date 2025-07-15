import axios, { AxiosError } from 'axios';
import { billingService } from './billing';

interface BillingError {
  code: string;
  message: string;
  details?: any;
  retryable: boolean;
}

class BillingServiceEnhanced {
  private retryCount = 0;
  private maxRetries = 3;
  private retryDelay = 1000; // Start with 1 second

  /**
   * Enhanced error handling for billing operations
   */
  private handleBillingError(error: AxiosError): BillingError {
    if (!error.response) {
      // Network error
      return {
        code: 'NETWORK_ERROR',
        message: 'Unable to connect to billing service. Please check your internet connection.',
        retryable: true
      };
    }

    const status = error.response.status;
    const data = error.response.data as any;

    // Handle specific error scenarios
    switch (status) {
      case 400:
        if (data?.detail?.includes('already have an active subscription')) {
          return {
            code: 'EXISTING_SUBSCRIPTION',
            message: 'You already have an active subscription. Visit the billing portal to manage it.',
            retryable: false
          };
        }
        return {
          code: 'INVALID_REQUEST',
          message: data?.detail || 'Invalid request. Please try again.',
          retryable: false
        };

      case 401:
        return {
          code: 'UNAUTHORIZED',
          message: 'Your session has expired. Please log in again.',
          retryable: false
        };

      case 403:
        if (data?.detail?.error === 'Upgrade required') {
          return {
            code: 'UPGRADE_REQUIRED',
            message: data.detail.message,
            details: {
              currentPlan: data.detail.current_plan,
              requiredPlan: data.detail.required_plan,
              upgradeUrl: data.detail.upgrade_url
            },
            retryable: false
          };
        }
        return {
          code: 'FORBIDDEN',
          message: 'You do not have permission to perform this action.',
          retryable: false
        };

      case 409:
        return {
          code: 'CONFLICT',
          message: 'Another operation is in progress. Please wait and try again.',
          retryable: true
        };

      case 429:
        return {
          code: 'RATE_LIMITED',
          message: 'Too many requests. Please wait a moment and try again.',
          retryable: true
        };

      case 500:
      case 502:
      case 503:
      case 504:
        return {
          code: 'SERVER_ERROR',
          message: 'Our billing service is temporarily unavailable. Please try again in a few moments.',
          retryable: true
        };

      default:
        return {
          code: 'UNKNOWN_ERROR',
          message: 'An unexpected error occurred. Please try again or contact support.',
          retryable: false
        };
    }
  }

  /**
   * Retry logic for failed requests
   */
  private async retryOperation<T>(
    operation: () => Promise<T>,
    context: string
  ): Promise<T> {
    try {
      const result = await operation();
      this.retryCount = 0; // Reset on success
      return result;
    } catch (error) {
      const billingError = this.handleBillingError(error as AxiosError);

      if (billingError.retryable && this.retryCount < this.maxRetries) {
        this.retryCount++;
        const delay = this.retryDelay * Math.pow(2, this.retryCount - 1); // Exponential backoff
        
        console.warn(`${context} failed, retrying in ${delay}ms... (attempt ${this.retryCount}/${this.maxRetries})`);
        
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.retryOperation(operation, context);
      }

      throw billingError;
    }
  }

  /**
   * Create checkout session with enhanced error handling
   */
  async createCheckoutSession(request: any): Promise<{ checkout_url: string }> {
    return this.retryOperation(
      () => billingService.createCheckoutSession(request),
      'Create checkout session'
    );
  }

  /**
   * Get subscription with caching
   */
  private subscriptionCache: { data: any; timestamp: number } | null = null;
  private cacheTimeout = 30000; // 30 seconds

  async getSubscription(forceRefresh = false): Promise<any> {
    if (!forceRefresh && this.subscriptionCache) {
      const age = Date.now() - this.subscriptionCache.timestamp;
      if (age < this.cacheTimeout) {
        return this.subscriptionCache.data;
      }
    }

    const subscription = await this.retryOperation(
      () => billingService.getSubscription(),
      'Get subscription'
    );

    this.subscriptionCache = {
      data: subscription,
      timestamp: Date.now()
    };

    return subscription;
  }

  /**
   * Get usage with smart caching based on plan
   */
  private usageCache: { data: any; timestamp: number } | null = null;

  async getUsage(forceRefresh = false): Promise<any> {
    const subscription = await this.getSubscription();
    const isFreePlan = subscription.plan === 'free';
    
    // Cache for longer if on a paid plan (less likely to hit limits)
    const cacheTimeout = isFreePlan ? 10000 : 60000; // 10s for free, 60s for paid

    if (!forceRefresh && this.usageCache) {
      const age = Date.now() - this.usageCache.timestamp;
      if (age < cacheTimeout) {
        return this.usageCache.data;
      }
    }

    const usage = await this.retryOperation(
      () => billingService.getUsage(),
      'Get usage'
    );

    this.usageCache = {
      data: usage,
      timestamp: Date.now()
    };

    return usage;
  }

  /**
   * Check if user can perform action with clear messaging
   */
  async checkFeatureAccess(feature: string): Promise<{ allowed: boolean; message?: string; upgradeUrl?: string }> {
    try {
      const subscription = await this.getSubscription();
      const allowed = billingService.isPremiumFeature(feature, subscription);

      if (!allowed) {
        const upgradeUrl = billingService.getUpgradeUrl(subscription.plan);
        return {
          allowed: false,
          message: `This feature requires a ${this.getRequiredPlan(feature)} plan or higher.`,
          upgradeUrl
        };
      }

      return { allowed: true };
    } catch (error) {
      console.error('Failed to check feature access:', error);
      return {
        allowed: false,
        message: 'Unable to verify feature access. Please try again.'
      };
    }
  }

  private getRequiredPlan(feature: string): string {
    const featurePlans: Record<string, string> = {
      'advanced_analytics': 'Professional',
      'api_access': 'Professional',
      'export': 'Professional',
      'team': 'Team'
    };
    return featurePlans[feature] || 'paid';
  }

  /**
   * Check usage with warnings at different thresholds
   */
  async checkUsageWithWarnings(metric: 'trades' | 'portfolios'): Promise<{
    allowed: boolean;
    usage: number;
    limit: number | null;
    percentageUsed: number;
    warning?: string;
    critical?: boolean;
  }> {
    try {
      const usage = await this.getUsage();
      const currentUsage = usage.usage[metric] || 0;
      const limit = usage.limits[`max_${metric}_per_month`] || 
                   usage.limits[`max_${metric}`];

      if (!limit) {
        // Unlimited
        return {
          allowed: true,
          usage: currentUsage,
          limit: null,
          percentageUsed: 0
        };
      }

      const percentageUsed = (currentUsage / limit) * 100;
      const remaining = limit - currentUsage;

      let warning: string | undefined;
      let critical = false;

      if (percentageUsed >= 100) {
        return {
          allowed: false,
          usage: currentUsage,
          limit,
          percentageUsed: 100,
          warning: `You've reached your ${metric} limit. Upgrade to continue.`,
          critical: true
        };
      } else if (percentageUsed >= 90) {
        warning = `Only ${remaining} ${metric} remaining this month!`;
        critical = true;
      } else if (percentageUsed >= 80) {
        warning = `You've used ${Math.round(percentageUsed)}% of your ${metric} this month.`;
      }

      return {
        allowed: true,
        usage: currentUsage,
        limit,
        percentageUsed,
        warning,
        critical
      };
    } catch (error) {
      console.error('Failed to check usage:', error);
      return {
        allowed: true, // Allow action if we can't verify
        usage: 0,
        limit: null,
        percentageUsed: 0,
        warning: 'Unable to verify usage limits.'
      };
    }
  }

  /**
   * Cancel subscription with confirmation
   */
  async cancelSubscriptionWithConfirmation(
    onConfirm: () => boolean | Promise<boolean>
  ): Promise<{ success: boolean; message: string }> {
    const confirmed = await onConfirm();
    if (!confirmed) {
      return {
        success: false,
        message: 'Cancellation aborted by user.'
      };
    }

    try {
      const result = await this.retryOperation(
        () => billingService.cancelSubscription(false), // Cancel at period end
        'Cancel subscription'
      );

      // Clear caches
      this.subscriptionCache = null;
      this.usageCache = null;

      return {
        success: true,
        message: 'Your subscription will be cancelled at the end of the billing period.'
      };
    } catch (error: any) {
      return {
        success: false,
        message: error.message || 'Failed to cancel subscription. Please try again or contact support.'
      };
    }
  }

  /**
   * Handle post-payment success with retries
   */
  async verifyPaymentSuccess(
    maxAttempts = 10,
    delayMs = 2000
  ): Promise<{ verified: boolean; subscription?: any }> {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const subscription = await this.getSubscription(true); // Force refresh
        
        if (subscription.status === 'active' || subscription.status === 'trialing') {
          return {
            verified: true,
            subscription
          };
        }
      } catch (error) {
        console.warn(`Payment verification attempt ${attempt} failed:`, error);
      }

      if (attempt < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }
    }

    return { verified: false };
  }

  /**
   * Clear all caches
   */
  clearCache(): void {
    this.subscriptionCache = null;
    this.usageCache = null;
    this.retryCount = 0;
  }
}

export const billingServiceEnhanced = new BillingServiceEnhanced();