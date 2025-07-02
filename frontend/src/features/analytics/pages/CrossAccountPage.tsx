
import React from 'react';
import CrossAccountDashboard from '../components/CrossAccountDashboard';
import GlobalLeaderboard from '../components/GlobalLeaderboard';

const CrossAccountPage: React.FC = () => {
  return (
    <div className="container mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Cross-Account Intelligence</h1>
        <p className="mt-2 text-gray-600">
          Analyze your performance across multiple trading accounts and see how you rank globally
        </p>
      </div>

      <div className="space-y-8">
        <CrossAccountDashboard />
        <GlobalLeaderboard />
      </div>
    </div>
  );
};

export default CrossAccountPage;
