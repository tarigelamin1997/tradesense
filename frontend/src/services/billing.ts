import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface CreateCheckoutRequest {
  plan: string;
  billing_cycle: string;
  success_url: string;
  cancel_url: string;
}

interface UpdatePlanRequest {
  plan: string;
  billing_cycle: string;
}

interface Subscription {
  id: string;
  plan: string;
  status: string;
  billing_cycle: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  trial_end?: string;
  limits: PlanLimits;
}

interface PlanLimits {
  max_trades_per_month?: number;
  max_portfolios?: number;
  data_retention_days?: number;
  max_api_calls_per_day?: number;
  max_team_members?: number;
  has_advanced_analytics: boolean;
  has_api_access: boolean;
  has_export_features: boolean;
  has_team_features: boolean;
  has_priority_support: boolean;
  has_white_label: boolean;
}

interface Usage {
  plan: string;
  usage: {
    trades: number;
    portfolios: number;
    api_calls: number;
    team_members: number;
  };
  limits: PlanLimits;
  percentage_used: {
    trades: number;
    portfolios: number;
    api_calls: number;
    team_members: number;
  };
}

interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: string;
  period: string;
  paid_at?: string;
  invoice_pdf?: string;
}

class BillingService {
  private getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async createCheckoutSession(request: CreateCheckoutRequest): Promise<{ checkout_url: string }> {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/billing/create-checkout-session`,
      request,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async createPortalSession(returnUrl: string): Promise<{ portal_url: string }> {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/billing/create-portal-session`,
      { return_url: returnUrl },
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async getSubscription(): Promise<Subscription> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/billing/subscription`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async getUsage(): Promise<Usage> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/billing/usage`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async updatePlan(request: UpdatePlanRequest): Promise<{ message: string }> {
    const response = await axios.put(
      `${API_BASE_URL}/api/v1/billing/update-plan`,
      request,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async cancelSubscription(cancelImmediately: boolean = false): Promise<{ message: string }> {
    const response = await axios.delete(
      `${API_BASE_URL}/api/v1/billing/cancel-subscription`,
      {
        params: { cancel_immediately: cancelImmediately },
        headers: this.getAuthHeaders()
      }
    );
    return response.data;
  }

  async getInvoices(limit: number = 10): Promise<Invoice[]> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/billing/invoices`,
      {
        params: { limit },
        headers: this.getAuthHeaders()
      }
    );
    return response.data;
  }

  // Helper methods
  isPremiumFeature(feature: string, subscription?: Subscription): boolean {
    if (!subscription) return false;
    
    const limits = subscription.limits;
    
    switch (feature) {
      case 'advanced_analytics':
        return limits.has_advanced_analytics;
      case 'api_access':
        return limits.has_api_access;
      case 'export':
        return limits.has_export_features;
      case 'team':
        return limits.has_team_features;
      default:
        return false;
    }
  }

  canAddMoreTrades(usage: Usage): boolean {
    if (!usage.limits.max_trades_per_month) return true; // Unlimited
    return usage.usage.trades < usage.limits.max_trades_per_month;
  }

  canAddMorePortfolios(usage: Usage): boolean {
    if (!usage.limits.max_portfolios) return true; // Unlimited
    return usage.usage.portfolios < usage.limits.max_portfolios;
  }

  formatPlanName(plan: string): string {
    const names: Record<string, string> = {
      free: 'Free',
      starter: 'Starter',
      professional: 'Professional',
      team: 'Team'
    };
    return names[plan] || plan;
  }

  formatBillingCycle(cycle: string): string {
    const cycles: Record<string, string> = {
      monthly: 'Monthly',
      yearly: 'Yearly',
      none: 'N/A'
    };
    return cycles[cycle] || cycle;
  }

  getUpgradeUrl(fromPlan: string): string {
    const planHierarchy = ['free', 'starter', 'professional', 'team'];
    const currentIndex = planHierarchy.indexOf(fromPlan);
    
    if (currentIndex < planHierarchy.length - 1) {
      const recommendedPlan = planHierarchy[currentIndex + 1];
      return `/checkout?plan=${recommendedPlan}`;
    }
    
    return '/pricing';
  }
}

export const billingService = new BillingService();