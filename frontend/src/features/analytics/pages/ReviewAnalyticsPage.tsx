
import React from 'react';
import { ReviewAnalyticsDashboard } from '../components/ReviewAnalyticsDashboard';

export const ReviewAnalyticsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ReviewAnalyticsDashboard />
      </div>
    </div>
  );
};
