import React from 'react';

interface TrustSignal {
  icon: React.ReactNode;
  text: string;
}

interface TrustBadgesProps {
  signals: TrustSignal[];
}

export default function TrustBadges({ signals }: TrustBadgesProps) {
  return (
    <div className="flex flex-wrap justify-center items-center gap-8">
      {signals.map((signal, idx) => (
        <div key={idx} className="flex items-center space-x-2 text-gray-600">
          {signal.icon}
          <span className="text-sm font-medium">{signal.text}</span>
        </div>
      ))}
      <div className="flex items-center space-x-2 text-gray-600">
        <img src="/stripe-badge.svg" alt="Stripe" className="h-6" />
        <span className="text-sm font-medium">Secure payments by Stripe</span>
      </div>
    </div>
  );
}