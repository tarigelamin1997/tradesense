
import React from 'react';
import AppLayout from '../../../components/layout/AppLayout';
import PlaybookComparisonDashboard from '../components/PlaybookComparisonDashboard';

const PlaybookComparisonPage: React.FC = () => {
  return (
    <AppLayout>
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Multi-Playbook Analysis
          </h1>
          <p className="mt-2 text-gray-600">
            Compare performance metrics across different trading strategies and playbooks
          </p>
        </div>
        
        <PlaybookComparisonDashboard />
      </div>
    </AppLayout>
  );
};

export default PlaybookComparisonPage;
