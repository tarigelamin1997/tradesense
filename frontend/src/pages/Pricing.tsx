import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, X, Shield, Award, TrendingUp, Users } from 'lucide-react';
import PricingCard from '../components/pricing/PricingCard';
import PricingToggle from '../components/pricing/PricingToggle';
import TrustBadges from '../components/pricing/TrustBadges';
import { useAuth } from '../hooks/useAuth';

const PLANS = [
  {
    id: 'starter',
    name: 'Starter',
    description: 'Perfect for individual traders getting started',
    monthlyPrice: 29,
    yearlyPrice: 290,
    features: [
      '100 trades per month',
      'Basic analytics',
      '30-day data retention',
      'Email support',
      '1 portfolio',
      'Mobile app access'
    ],
    limitations: [
      'No API access',
      'No advanced analytics',
      'No export features'
    ],
    cta: 'Start Trading',
    highlighted: false,
    icon: <TrendingUp className="w-6 h-6" />
  },
  {
    id: 'professional',
    name: 'Professional',
    description: 'For serious traders who need advanced tools',
    monthlyPrice: 99,
    yearlyPrice: 990,
    features: [
      'Unlimited trades',
      'Advanced analytics & charts',
      'Unlimited data retention',
      'Priority support',
      '5 portfolios',
      'API access (1,000 calls/day)',
      'Export to Excel/PDF',
      'Custom alerts',
      'Real-time sync'
    ],
    limitations: [
      'Single user only',
      'No team features'
    ],
    cta: 'Go Professional',
    highlighted: true,
    badge: 'MOST POPULAR',
    icon: <Award className="w-6 h-6" />
  },
  {
    id: 'team',
    name: 'Team',
    description: 'For trading teams and small funds',
    monthlyPrice: 299,
    yearlyPrice: 2990,
    features: [
      'Everything in Professional',
      '5 user seats',
      'Team performance dashboard',
      'Shared strategies & templates',
      'Admin controls',
      'API access (10,000 calls/day)',
      'White-label options',
      'Dedicated account manager',
      'Custom integrations',
      'SLA guarantee'
    ],
    limitations: [],
    cta: 'Start Team Trial',
    highlighted: false,
    icon: <Users className="w-6 h-6" />
  }
];

const TRUST_SIGNALS = [
  {
    icon: <Shield className="w-5 h-5" />,
    text: '256-bit SSL encryption'
  },
  {
    icon: <Shield className="w-5 h-5" />,
    text: 'SOC2 compliant'
  },
  {
    icon: <Shield className="w-5 h-5" />,
    text: 'PCI DSS certified'
  }
];

const TESTIMONIALS = [
  {
    name: 'Sarah Chen',
    role: 'Day Trader',
    image: '/avatars/sarah.jpg',
    content: 'TradeSense helped me identify patterns in my trading that I never noticed before. My win rate improved by 15% in just 2 months.',
    rating: 5
  },
  {
    name: 'Mike Johnson',
    role: 'Swing Trader',
    image: '/avatars/mike.jpg',
    content: 'The analytics are incredible. I can finally see which strategies work and which don\'t. Worth every penny.',
    rating: 5
  },
  {
    name: 'Trading Alpha Fund',
    role: 'Hedge Fund',
    image: '/avatars/fund.jpg',
    content: 'Our team uses TradeSense to track performance across all traders. The team features are exactly what we needed.',
    rating: 5
  }
];

const FAQ = [
  {
    question: 'Can I change plans anytime?',
    answer: 'Yes! You can upgrade or downgrade your plan at any time. When upgrading, you\'ll be charged a prorated amount. When downgrading, you\'ll receive credit for the unused time.'
  },
  {
    question: 'What happens after my free trial?',
    answer: 'After your 14-day free trial, you\'ll be automatically downgraded to our free tier unless you choose a paid plan. No credit card required for the trial.'
  },
  {
    question: 'Do you offer refunds?',
    answer: 'Yes, we offer a 30-day money-back guarantee. If you\'re not satisfied with TradeSense, contact us within 30 days for a full refund.'
  },
  {
    question: 'Can I export my data?',
    answer: 'Professional and Team plans include full data export capabilities. You can export your trades, analytics, and reports in CSV, Excel, or PDF format.'
  }
];

export default function Pricing() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleSelectPlan = (planId: string) => {
    if (!user) {
      navigate('/auth/register', { state: { plan: planId, billing: billingCycle } });
    } else {
      navigate('/checkout', { state: { plan: planId, billing: billingCycle } });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Choose Your Trading Edge
            </h1>
            <p className="text-xl opacity-90 mb-8">
              Start with a 14-day free trial. No credit card required.
            </p>
            <div className="flex items-center justify-center space-x-8 text-sm">
              <div className="flex items-center">
                <Check className="w-5 h-5 mr-2" />
                <span>14-day free trial</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 mr-2" />
                <span>Cancel anytime</span>
              </div>
              <div className="flex items-center">
                <Check className="w-5 h-5 mr-2" />
                <span>No setup fees</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Toggle */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8">
        <div className="flex justify-center">
          <PricingToggle
            billingCycle={billingCycle}
            onChange={setBillingCycle}
          />
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {PLANS.map((plan) => (
            <PricingCard
              key={plan.id}
              plan={plan}
              billingCycle={billingCycle}
              onSelect={() => handleSelectPlan(plan.id)}
            />
          ))}
        </div>
      </div>

      {/* Trust Badges */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <TrustBadges signals={TRUST_SIGNALS} />
      </div>

      {/* Detailed Feature Comparison */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">
          Detailed Feature Comparison
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-4 px-6">Features</th>
                <th className="text-center py-4 px-6">Starter</th>
                <th className="text-center py-4 px-6 bg-blue-50">Professional</th>
                <th className="text-center py-4 px-6">Team</th>
              </tr>
            </thead>
            <tbody>
              {[
                { feature: 'Trades per month', starter: '100', professional: 'Unlimited', team: 'Unlimited' },
                { feature: 'Data retention', starter: '30 days', professional: 'Unlimited', team: 'Unlimited' },
                { feature: 'Portfolios', starter: '1', professional: '5', team: 'Unlimited' },
                { feature: 'Advanced analytics', starter: false, professional: true, team: true },
                { feature: 'API access', starter: false, professional: '1,000/day', team: '10,000/day' },
                { feature: 'Export features', starter: false, professional: true, team: true },
                { feature: 'Team seats', starter: '1', professional: '1', team: '5' },
                { feature: 'Priority support', starter: false, professional: true, team: true },
                { feature: 'White-label', starter: false, professional: false, team: true },
              ].map((row, idx) => (
                <tr key={idx} className="border-b">
                  <td className="py-4 px-6 font-medium">{row.feature}</td>
                  <td className="py-4 px-6 text-center">
                    {typeof row.starter === 'boolean' ? (
                      row.starter ? <Check className="w-5 h-5 text-green-500 mx-auto" /> : <X className="w-5 h-5 text-gray-300 mx-auto" />
                    ) : (
                      <span className="text-gray-700">{row.starter}</span>
                    )}
                  </td>
                  <td className="py-4 px-6 text-center bg-blue-50">
                    {typeof row.professional === 'boolean' ? (
                      row.professional ? <Check className="w-5 h-5 text-green-500 mx-auto" /> : <X className="w-5 h-5 text-gray-300 mx-auto" />
                    ) : (
                      <span className="text-gray-700">{row.professional}</span>
                    )}
                  </td>
                  <td className="py-4 px-6 text-center">
                    {typeof row.team === 'boolean' ? (
                      row.team ? <Check className="w-5 h-5 text-green-500 mx-auto" /> : <X className="w-5 h-5 text-gray-300 mx-auto" />
                    ) : (
                      <span className="text-gray-700">{row.team}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Testimonials */}
      <div className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">
            Trusted by 1,000+ Traders
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {TESTIMONIALS.map((testimonial, idx) => (
              <div key={idx} className="bg-gray-50 rounded-lg p-6">
                <div className="flex items-center mb-4">
                  <div className="w-12 h-12 bg-gray-300 rounded-full mr-4"></div>
                  <div>
                    <div className="font-semibold">{testimonial.name}</div>
                    <div className="text-sm text-gray-600">{testimonial.role}</div>
                  </div>
                </div>
                <div className="flex mb-3">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <span key={i} className="text-yellow-400">★</span>
                  ))}
                </div>
                <p className="text-gray-700">{testimonial.content}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* FAQ */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">
          Frequently Asked Questions
        </h2>
        <div className="space-y-6">
          {FAQ.map((item, idx) => (
            <div key={idx} className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="font-semibold text-lg mb-2">{item.question}</h3>
              <p className="text-gray-700">{item.answer}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div className="bg-blue-600 text-white py-16">
        <div className="max-w-4xl mx-auto text-center px-4">
          <h2 className="text-3xl font-bold mb-4">
            Ready to Improve Your Trading?
          </h2>
          <p className="text-xl mb-8 opacity-90">
            Join thousands of traders who are already using TradeSense to track, analyze, and improve their performance.
          </p>
          <button
            onClick={() => handleSelectPlan('professional')}
            className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-colors"
          >
            Start Your Free Trial
          </button>
          <p className="mt-4 text-sm opacity-75">
            No credit card required • 14-day free trial • Cancel anytime
          </p>
        </div>
      </div>
    </div>
  );
}