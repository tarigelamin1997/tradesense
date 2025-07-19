import { api } from './client';

export interface Subscription {
	id: string;
	user_id: number;
	stripe_subscription_id?: string;
	stripe_customer_id?: string;
	status: 'active' | 'canceled' | 'past_due' | 'trialing';
	plan_id: string;
	current_period_start: string;
	current_period_end: string;
	created_at: string;
	updated_at?: string;
}

export interface Usage {
	user_id: number;
	period_start: string;
	period_end: string;
	trades_count: number;
	trades_limit: number;
	api_calls_count: number;
	api_calls_limit: number;
}

export interface CheckoutSessionData {
	productId: string;
	successUrl: string;
	cancelUrl: string;
}

export interface CheckoutSession {
	url: string;
	session_id: string;
}

export interface BillingPortalSession {
	url: string;
	session_id: string;
}

class BillingAPI {
	// Get current subscription
	async getSubscription(): Promise<Subscription | null> {
		try {
			return await api.get<Subscription>('/api/v1/billing/subscription');
		} catch (error: any) {
			if (error.status === 404) {
				return null; // No subscription
			}
			throw error;
		}
	}
	
	// Get usage statistics
	async getUsage(): Promise<Usage> {
		return await api.get<Usage>('/api/v1/billing/usage');
	}
	
	// Create checkout session
	async createCheckoutSession(data: CheckoutSessionData): Promise<CheckoutSession> {
		return await api.post<CheckoutSession>('/api/v1/billing/create-checkout-session', data);
	}
	
	// Create billing portal session
	async createPortalSession(): Promise<BillingPortalSession> {
		return await api.post<BillingPortalSession>('/api/v1/billing/create-portal-session');
	}
	
	// Cancel subscription
	async cancelSubscription(): Promise<Subscription> {
		return await api.post<Subscription>('/api/v1/billing/cancel-subscription');
	}
	
	// Resume subscription
	async resumeSubscription(): Promise<Subscription> {
		return await api.post<Subscription>('/api/v1/billing/resume-subscription');
	}
}

export const billingApi = new BillingAPI();