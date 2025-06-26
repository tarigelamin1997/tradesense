import React from 'react';
import PlaybookComparisonDashboard from '../components/PlaybookComparisonDashboard';

const PlaybookComparisonPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <PlaybookComparisonDashboard />
      </div>
    </div>
  );
};

export default PlaybookComparisonPage;