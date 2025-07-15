import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';
import { billingServiceEnhanced } from '../services/billingEnhanced';
import Checkout from '../pages/Checkout';
import Pricing from '../pages/Pricing';
import BillingPortal from '../pages/BillingPortal';
import FeatureGateEnhanced from '../components/FeatureGateEnhanced';
import UsageLimiterEnhanced from '../components/UsageLimiterEnhanced';

// Mock dependencies
jest.mock('axios');
jest.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: { id: 1, email: 'test@example.com' } })
}));

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({ state: { plan: 'professional', billing: 'monthly' } })
}));

describe('Billing Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    billingServiceEnhanced.clearCache();
    
    // Mock window.location
    delete window.location;
    window.location = { href: '', origin: 'http://localhost:3000' } as any;
  });

  describe('Scenario 1: New User → Free Trial → Paid', () => {
    test('should complete checkout flow successfully', async () => {
      const mockCheckoutUrl = 'https://checkout.stripe.com/session123';
      
      (axios.post as jest.Mock).mockResolvedValueOnce({
        data: { checkout_url: mockCheckoutUrl }
      });

      const { getByText, getByRole } = render(
        <BrowserRouter>
          <Checkout />
        </BrowserRouter>
      );

      // Check order summary
      expect(getByText('Professional Plan')).toBeInTheDocument();
      expect(getByText('$99/mo')).toBeInTheDocument();

      // Click checkout button
      const checkoutBtn = getByRole('button', { name: /continue to secure checkout/i });
      fireEvent.click(checkoutBtn);

      // Should show loading state
      expect(getByText('Processing...')).toBeInTheDocument();

      // Wait for redirect
      await waitFor(() => {
        expect(window.location.href).toBe(mockCheckoutUrl);
      });
    });

    test('should handle checkout session creation failure', async () => {
      (axios.post as jest.Mock).mockRejectedValueOnce({
        response: {
          status: 400,
          data: { detail: 'You already have an active subscription' }
        }
      });

      const { getByText, getByRole } = render(
        <BrowserRouter>
          <Checkout />
        </BrowserRouter>
      );

      const checkoutBtn = getByRole('button', { name: /continue to secure checkout/i });
      fireEvent.click(checkoutBtn);

      await waitFor(() => {
        expect(getByText(/already have an active subscription/i)).toBeInTheDocument();
      });
    });

    test('should verify payment success with retries', async () => {
      // First call returns free plan
      (axios.get as jest.Mock)
        .mockResolvedValueOnce({
          data: { plan: 'free', status: 'active' }
        })
        .mockResolvedValueOnce({
          data: { plan: 'professional', status: 'trialing' }
        });

      const result = await billingServiceEnhanced.verifyPaymentSuccess(3, 100);
      
      expect(result.verified).toBe(true);
      expect(result.subscription?.plan).toBe('professional');
      expect(axios.get).toHaveBeenCalledTimes(2);
    });
  });

  describe('Scenario 2: Free User Hits Limits', () => {
    test('should show upgrade prompt when limit reached', async () => {
      (axios.get as jest.Mock).mockResolvedValueOnce({
        data: {
          plan: 'free',
          usage: { trades: 10 },
          limits: { max_trades_per_month: 10 },
          percentage_used: { trades: 100 }
        }
      });

      const { getByText } = render(
        <UsageLimiterEnhanced metric="trades">
          {({ canProceed }) => (
            canProceed ? <button>Add Trade</button> : <div>Limit Reached</div>
          )}
        </UsageLimiterEnhanced>
      );

      await waitFor(() => {
        expect(getByText('Limit Reached')).toBeInTheDocument();
      });
    });

    test('should show warning at 90% usage', async () => {
      (axios.get as jest.Mock).mockResolvedValueOnce({
        data: {
          plan: 'free',
          usage: { trades: 9 },
          limits: { max_trades_per_month: 10 },
          percentage_used: { trades: 90 }
        }
      });

      const { getByText } = render(
        <UsageLimiterEnhanced metric="trades" showInlineWarning>
          {() => <div>Content</div>}
        </UsageLimiterEnhanced>
      );

      await waitFor(() => {
        expect(getByText(/only 1 trades remaining/i)).toBeInTheDocument();
      });
    });
  });

  describe('Scenario 3: Payment Failures', () => {
    test('should handle declined card gracefully', async () => {
      (axios.post as jest.Mock).mockRejectedValueOnce({
        response: {
          status: 400,
          data: { detail: 'Your card was declined' }
        }
      });

      const { getByRole, getByText } = render(
        <BrowserRouter>
          <Checkout />
        </BrowserRouter>
      );

      fireEvent.click(getByRole('button', { name: /continue to secure checkout/i }));

      await waitFor(() => {
        expect(getByText(/your card was declined/i)).toBeInTheDocument();
      });
    });

    test('should retry on network errors', async () => {
      (axios.post as jest.Mock)
        .mockRejectedValueOnce({ code: 'ECONNABORTED' })
        .mockResolvedValueOnce({
          data: { checkout_url: 'https://checkout.stripe.com/success' }
        });

      const result = await billingServiceEnhanced.createCheckoutSession({
        plan: 'professional',
        billing_cycle: 'monthly'
      });

      expect(result.checkout_url).toBe('https://checkout.stripe.com/success');
      expect(axios.post).toHaveBeenCalledTimes(2);
    });
  });

  describe('Scenario 4: Subscription Management', () => {
    test('should display current subscription correctly', async () => {
      (axios.get as jest.Mock).mockResolvedValue({
        data: {
          plan: 'professional',
          status: 'active',
          current_period_end: '2024-02-01T00:00:00Z',
          usage: { trades: 50 },
          limits: { max_trades_per_month: null }
        }
      });

      const { getByText } = render(
        <BrowserRouter>
          <BillingPortal />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(getByText('Professional')).toBeInTheDocument();
        expect(getByText(/50 \/ Unlimited/)).toBeInTheDocument();
      });
    });

    test('should handle subscription cancellation', async () => {
      (axios.delete as jest.Mock).mockResolvedValueOnce({
        data: { message: 'Subscription cancelled successfully' }
      });

      const result = await billingServiceEnhanced.cancelSubscriptionWithConfirmation(
        async () => true
      );

      expect(result.success).toBe(true);
      expect(result.message).toContain('cancelled at the end of the billing period');
    });
  });

  describe('Scenario 5: Feature Gating', () => {
    test('should block access to premium features for free users', async () => {
      (axios.get as jest.Mock).mockResolvedValueOnce({
        data: {
          plan: 'free',
          status: 'active',
          limits: { has_advanced_analytics: false }
        }
      });

      const { getByText } = render(
        <BrowserRouter>
          <FeatureGateEnhanced feature="advanced_analytics">
            <div>Premium Content</div>
          </FeatureGateEnhanced>
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(getByText(/advanced analytics is a premium feature/i)).toBeInTheDocument();
        expect(screen.queryByText('Premium Content')).not.toBeInTheDocument();
      });
    });

    test('should allow access for subscribed users', async () => {
      (axios.get as jest.Mock).mockResolvedValueOnce({
        data: {
          plan: 'professional',
          status: 'active',
          limits: { has_advanced_analytics: true }
        }
      });

      const { getByText } = render(
        <BrowserRouter>
          <FeatureGateEnhanced feature="advanced_analytics">
            <div>Premium Content</div>
          </FeatureGateEnhanced>
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(getByText('Premium Content')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    test('should handle expired trials', async () => {
      (axios.get as jest.Mock).mockResolvedValueOnce({
        data: {
          plan: 'free',
          status: 'active',
          trial_end: '2024-01-01T00:00:00Z'
        }
      });

      const { getByText } = render(
        <BrowserRouter>
          <BillingPortal />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(getByText('Free')).toBeInTheDocument();
        expect(getByText(/upgrade plan/i)).toBeInTheDocument();
      });
    });

    test('should handle subscription in past_due state', async () => {
      (axios.get as jest.Mock).mockResolvedValueOnce({
        data: {
          plan: 'professional',
          status: 'past_due',
          current_period_end: '2024-02-01T00:00:00Z'
        }
      });

      const { container } = render(
        <BrowserRouter>
          <BillingPortal />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(container.textContent).toContain('Professional');
        // Should show some indication of payment issue
      });
    });

    test('should cache subscription data appropriately', async () => {
      (axios.get as jest.Mock).mockResolvedValueOnce({
        data: { plan: 'professional', status: 'active' }
      });

      // First call
      await billingServiceEnhanced.getSubscription();
      
      // Second call within cache timeout
      await billingServiceEnhanced.getSubscription();
      
      // Should only make one API call
      expect(axios.get).toHaveBeenCalledTimes(1);
      
      // Force refresh
      await billingServiceEnhanced.getSubscription(true);
      
      // Now should have made two calls
      expect(axios.get).toHaveBeenCalledTimes(2);
    });
  });
});