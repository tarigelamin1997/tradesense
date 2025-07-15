import React from 'react';

interface PricingToggleProps {
  billingCycle: 'monthly' | 'yearly';
  onChange: (cycle: 'monthly' | 'yearly') => void;
}

export default function PricingToggle({ billingCycle, onChange }: PricingToggleProps) {
  return (
    <div className="bg-white rounded-full shadow-md p-1 inline-flex">
      <button
        onClick={() => onChange('monthly')}
        className={`px-6 py-2 rounded-full font-medium transition-all ${
          billingCycle === 'monthly'
            ? 'bg-blue-600 text-white'
            : 'text-gray-700 hover:text-gray-900'
        }`}
      >
        Monthly
      </button>
      <button
        onClick={() => onChange('yearly')}
        className={`px-6 py-2 rounded-full font-medium transition-all flex items-center ${
          billingCycle === 'yearly'
            ? 'bg-blue-600 text-white'
            : 'text-gray-700 hover:text-gray-900'
        }`}
      >
        Yearly
        <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${
          billingCycle === 'yearly'
            ? 'bg-blue-500 text-white'
            : 'bg-green-100 text-green-700'
        }`}>
          Save 17%
        </span>
      </button>
    </div>
  );
}