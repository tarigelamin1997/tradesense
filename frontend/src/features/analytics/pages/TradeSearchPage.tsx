
import React from 'react';
import { TradeSearchDashboard } from '../components/TradeSearchDashboard';

export const TradeSearchPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Trade Journal Search</h1>
          <p className="mt-2 text-gray-600">
            Find specific trades, review patterns, and learn from your trading history
          </p>
        </div>
        
        <TradeSearchDashboard />
      </div>
    </div>
  );
};

export default TradeSearchPage;
