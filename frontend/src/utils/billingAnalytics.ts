interface AnalyticsEvent {
  event: string;
  properties?: Record<string, any>;
}

/**
 * Billing Analytics Tracking
 * 
 * Tracks key conversion events for optimization
 */
class BillingAnalytics {
  private queue: AnalyticsEvent[] = [];
  private isInitialized = false;

  /**
   * Initialize analytics with Google Analytics or other provider
   */
  initialize() {
    // Check if gtag is available
    if (typeof window !== 'undefined' && window.gtag) {
      this.isInitialized = true;
      this.flushQueue();
    } else {
      console.warn('Analytics not initialized - gtag not found');
    }
  }

  /**
   * Track a billing event
   */
  track(event: string, properties?: Record<string, any>) {
    const analyticsEvent: AnalyticsEvent = { event, properties };

    if (this.isInitialized && window.gtag) {
      window.gtag('event', event, properties);
    } else {
      // Queue events until analytics is ready
      this.queue.push(analyticsEvent);
    }

    // Also log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log('[Analytics]', event, properties);
    }
  }

  /**
   * Flush queued events
   */
  private flushQueue() {
    while (this.queue.length > 0) {
      const event = this.queue.shift();
      if (event && window.gtag) {
        window.gtag('event', event.event, event.properties);
      }
    }
  }

  // Pricing Page Events
  pricingPageViewed(source?: string) {
    this.track('pricing_page_viewed', {
      source,
      timestamp: new Date().toISOString()
    });
  }

  planSelected(plan: string, billingCycle: 'monthly' | 'yearly') {
    this.track('plan_selected', {
      plan,
      billing_cycle: billingCycle,
      potential_revenue: this.calculateRevenue(plan, billingCycle)
    });
  }

  billingToggleChanged(newCycle: 'monthly' | 'yearly') {
    this.track('billing_toggle_changed', {
      new_cycle: newCycle
    });
  }

  // Checkout Events
  checkoutStarted(plan: string, billingCycle: string) {
    this.track('checkout_started', {
      plan,
      billing_cycle: billingCycle,
      value: this.calculateRevenue(plan, billingCycle)
    });
  }

  checkoutCompleted(plan: string, billingCycle: string, trialDays?: number) {
    this.track('checkout_completed', {
      plan,
      billing_cycle: billingCycle,
      trial_days: trialDays,
      value: this.calculateRevenue(plan, billingCycle)
    });

    // Also track as conversion
    this.track('conversion', {
      plan,
      billing_cycle: billingCycle
    });
  }

  checkoutAbandoned(plan: string, reason?: string) {
    this.track('checkout_abandoned', {
      plan,
      reason,
      potential_loss: this.calculateRevenue(plan, 'monthly')
    });
  }

  checkoutError(error: string, plan?: string) {
    this.track('checkout_error', {
      error_message: error,
      plan
    });
  }

  // Feature Gate Events
  featureGateShown(feature: string, currentPlan: string) {
    this.track('feature_gate_shown', {
      feature,
      current_plan: currentPlan,
      upgrade_potential: true
    });
  }

  upgradePromptClicked(trigger: string, feature?: string) {
    this.track('upgrade_prompt_clicked', {
      trigger,
      feature,
      intent: 'high'
    });
  }

  // Usage Events
  usageLimitApproaching(metric: string, percentage: number, plan: string) {
    this.track('usage_limit_approaching', {
      metric,
      percentage,
      plan,
      risk_of_churn: percentage < 90 ? 'low' : 'high'
    });
  }

  usageLimitReached(metric: string, plan: string) {
    this.track('usage_limit_reached', {
      metric,
      plan,
      upgrade_opportunity: true
    });
  }

  // Subscription Management Events
  billingPortalAccessed() {
    this.track('billing_portal_accessed', {
      intent: 'manage_subscription'
    });
  }

  subscriptionCancelled(plan: string, reason?: string) {
    this.track('subscription_cancelled', {
      plan,
      reason,
      churn: true
    });
  }

  subscriptionReactivated(plan: string) {
    this.track('subscription_reactivated', {
      plan,
      win_back: true
    });
  }

  planChanged(fromPlan: string, toPlan: string) {
    const isUpgrade = this.isPlanUpgrade(fromPlan, toPlan);
    
    this.track('plan_changed', {
      from_plan: fromPlan,
      to_plan: toPlan,
      change_type: isUpgrade ? 'upgrade' : 'downgrade',
      revenue_impact: isUpgrade ? 'positive' : 'negative'
    });
  }

  // Payment Events
  paymentFailed(plan: string, errorType: string) {
    this.track('payment_failed', {
      plan,
      error_type: errorType,
      churn_risk: 'high'
    });
  }

  paymentRecovered(plan: string, attemptNumber: number) {
    this.track('payment_recovered', {
      plan,
      attempt_number: attemptNumber,
      saved_revenue: this.calculateRevenue(plan, 'monthly')
    });
  }

  // Trial Events
  trialStarted(plan: string) {
    this.track('trial_started', {
      plan,
      trial_length: 14
    });
  }

  trialEnding(plan: string, daysRemaining: number) {
    this.track('trial_ending', {
      plan,
      days_remaining: daysRemaining,
      conversion_opportunity: true
    });
  }

  trialConverted(plan: string, billingCycle: string) {
    this.track('trial_converted', {
      plan,
      billing_cycle: billingCycle,
      ltv_potential: this.calculateLTV(plan, billingCycle)
    });
  }

  // Helper Methods
  private calculateRevenue(plan: string, cycle: string): number {
    const prices: Record<string, { monthly: number; yearly: number }> = {
      starter: { monthly: 29, yearly: 290 },
      professional: { monthly: 99, yearly: 990 },
      team: { monthly: 299, yearly: 2990 }
    };

    const planPrices = prices[plan.toLowerCase()];
    if (!planPrices) return 0;

    return cycle === 'yearly' ? planPrices.yearly : planPrices.monthly;
  }

  private calculateLTV(plan: string, cycle: string): number {
    const monthlyRevenue = this.calculateRevenue(plan, 'monthly');
    const averageLifetimeMonths = 24; // Assume 2-year average lifetime
    
    return monthlyRevenue * averageLifetimeMonths;
  }

  private isPlanUpgrade(fromPlan: string, toPlan: string): boolean {
    const planHierarchy = ['free', 'starter', 'professional', 'team'];
    const fromIndex = planHierarchy.indexOf(fromPlan.toLowerCase());
    const toIndex = planHierarchy.indexOf(toPlan.toLowerCase());
    
    return toIndex > fromIndex;
  }

  // A/B Testing Support
  recordExperiment(experimentName: string, variant: string) {
    this.track('experiment_viewed', {
      experiment_name: experimentName,
      variant,
      timestamp: new Date().toISOString()
    });
  }

  // Session Recording
  startSession() {
    const sessionId = Math.random().toString(36).substring(7);
    sessionStorage.setItem('billing_session_id', sessionId);
    
    this.track('billing_session_started', {
      session_id: sessionId
    });
    
    return sessionId;
  }

  endSession(converted: boolean) {
    const sessionId = sessionStorage.getItem('billing_session_id');
    
    this.track('billing_session_ended', {
      session_id: sessionId,
      converted,
      session_duration: this.getSessionDuration()
    });
  }

  private getSessionDuration(): number {
    // Calculate session duration in seconds
    // This would need proper implementation with session start time
    return 0;
  }
}

// Create singleton instance
export const billingAnalytics = new BillingAnalytics();

// Initialize on load
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    billingAnalytics.initialize();
  });
}

// Export convenience functions
export const trackPricingView = (source?: string) => 
  billingAnalytics.pricingPageViewed(source);

export const trackPlanSelection = (plan: string, cycle: 'monthly' | 'yearly') => 
  billingAnalytics.planSelected(plan, cycle);

export const trackCheckoutStart = (plan: string, cycle: string) => 
  billingAnalytics.checkoutStarted(plan, cycle);

export const trackConversion = (plan: string, cycle: string) => 
  billingAnalytics.checkoutCompleted(plan, cycle);

export const trackFeatureGate = (feature: string, plan: string) => 
  billingAnalytics.featureGateShown(feature, plan);

export const trackUpgradeIntent = (trigger: string, feature?: string) => 
  billingAnalytics.upgradePromptClicked(trigger, feature);