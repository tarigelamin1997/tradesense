
import React from 'react';
import EdgeStrengthDashboard from '../components/EdgeStrengthDashboard';

const EdgeStrengthPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <EdgeStrengthDashboard />
      </div>
    </div>
  );
};

export default EdgeStrengthPage;
