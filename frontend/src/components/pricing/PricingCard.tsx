import React from 'react';
import { Check, X } from 'lucide-react';

interface PricingCardProps {
  plan: {
    id: string;
    name: string;
    description: string;
    monthlyPrice: number;
    yearlyPrice: number;
    features: string[];
    limitations: string[];
    cta: string;
    highlighted: boolean;
    badge?: string;
    icon?: React.ReactNode;
  };
  billingCycle: 'monthly' | 'yearly';
  onSelect: () => void;
}

export default function PricingCard({ plan, billingCycle, onSelect }: PricingCardProps) {
  const price = billingCycle === 'monthly' ? plan.monthlyPrice : plan.yearlyPrice;
  const isYearly = billingCycle === 'yearly';
  const monthlySavings = isYearly ? Math.round((plan.monthlyPrice * 12 - plan.yearlyPrice) / 12) : 0;

  return (
    <div className={`relative bg-white rounded-2xl shadow-lg overflow-hidden transition-transform hover:scale-105 ${
      plan.highlighted ? 'ring-2 ring-blue-600' : ''
    }`}>
      {plan.badge && (
        <div className="absolute top-0 right-0 bg-blue-600 text-white px-4 py-1 text-sm font-semibold rounded-bl-lg">
          {plan.badge}
        </div>
      )}
      
      <div className="p-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
            <p className="text-gray-600 mt-1">{plan.description}</p>
          </div>
          {plan.icon && (
            <div className="text-blue-600">
              {plan.icon}
            </div>
          )}
        </div>
        
        <div className="mb-6">
          <div className="flex items-baseline">
            <span className="text-4xl font-bold text-gray-900">${price}</span>
            <span className="ml-2 text-gray-600">
              /{billingCycle === 'monthly' ? 'month' : 'year'}
            </span>
          </div>
          {isYearly && monthlySavings > 0 && (
            <p className="text-sm text-green-600 mt-1">
              Save ${monthlySavings}/month with yearly billing
            </p>
          )}
        </div>
        
        <button
          onClick={onSelect}
          className={`w-full py-3 px-6 rounded-lg font-semibold transition-colors ${
            plan.highlighted
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
          }`}
        >
          {plan.cta}
        </button>
        
        <div className="mt-8 space-y-4">
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">What's included:</h4>
            <ul className="space-y-3">
              {plan.features.map((feature, idx) => (
                <li key={idx} className="flex items-start">
                  <Check className="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{feature}</span>
                </li>
              ))}
            </ul>
          </div>
          
          {plan.limitations.length > 0 && (
            <div className="pt-4 border-t border-gray-200">
              <ul className="space-y-2">
                {plan.limitations.map((limitation, idx) => (
                  <li key={idx} className="flex items-start">
                    <X className="w-5 h-5 text-gray-300 mr-3 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-500">{limitation}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}