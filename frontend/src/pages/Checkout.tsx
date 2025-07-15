import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Loader2, CreditCard, Shield } from 'lucide-react';
import { billingService } from '../services/billing';
import { useAuth } from '../hooks/useAuth';

export default function Checkout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { plan, billing } = location.state || { plan: 'professional', billing: 'monthly' };

  const planDetails = {
    starter: {
      name: 'Starter',
      monthly: 29,
      yearly: 290
    },
    professional: {
      name: 'Professional',
      monthly: 99,
      yearly: 990
    },
    team: {
      name: 'Team',
      monthly: 299,
      yearly: 2990
    }
  };

  const selectedPlan = planDetails[plan as keyof typeof planDetails];
  const price = billing === 'monthly' ? selectedPlan.monthly : selectedPlan.yearly;

  useEffect(() => {
    if (!user) {
      navigate('/auth/login', { state: { from: location } });
    }
  }, [user, navigate, location]);

  const handleCheckout = async () => {
    setLoading(true);
    setError('');

    try {
      const { checkout_url } = await billingService.createCheckoutSession({
        plan,
        billing_cycle: billing,
        success_url: `${window.location.origin}/payment-success`,
        cancel_url: `${window.location.origin}/pricing`
      });

      // Redirect to Stripe Checkout
      window.location.href = checkout_url;
    } catch (err: any) {
      setError(err.message || 'Failed to create checkout session');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">
            Complete Your Subscription
          </h1>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}

          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-4">Order Summary</h2>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium">{selectedPlan.name} Plan</span>
                <span className="font-semibold">${price}/{billing === 'monthly' ? 'mo' : 'yr'}</span>
              </div>
              <div className="text-sm text-gray-600">
                {billing === 'yearly' && (
                  <p className="text-green-600">You save ${(selectedPlan.monthly * 12 - selectedPlan.yearly)} per year!</p>
                )}
              </div>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="font-semibold mb-3">What happens next?</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start">
                <span className="mr-2">1.</span>
                <span>You'll be redirected to Stripe's secure checkout</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">2.</span>
                <span>Enter your payment information</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">3.</span>
                <span>Start your 14-day free trial immediately</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">4.</span>
                <span>Cancel anytime before trial ends to avoid charges</span>
              </li>
            </ul>
          </div>

          <button
            onClick={handleCheckout}
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <CreditCard className="w-5 h-5 mr-2" />
                Continue to Secure Checkout
              </>
            )}
          </button>

          <div className="mt-6 text-center">
            <div className="flex items-center justify-center text-sm text-gray-500 mb-2">
              <Shield className="w-4 h-4 mr-2" />
              <span>Secure checkout powered by Stripe</span>
            </div>
            <p className="text-xs text-gray-400">
              Your payment information is encrypted and secure. We never store your card details.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}