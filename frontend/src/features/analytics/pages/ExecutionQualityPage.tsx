
import React from 'react';
import ExecutionQualityDashboard from '../components/ExecutionQualityDashboard';

const ExecutionQualityPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <ExecutionQualityDashboard />
      </div>
    </div>
  );
};

export default ExecutionQualityPage;
