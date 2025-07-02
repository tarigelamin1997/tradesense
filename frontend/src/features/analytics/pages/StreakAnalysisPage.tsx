
import React from 'react';
import { StreakAnalysisDashboard } from '../components/StreakAnalysisDashboard';

export const StreakAnalysisPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Streak & Consistency Analysis</h1>
          <p className="mt-2 text-gray-600">
            Understand your performance rhythm and make data-driven risk decisions
          </p>
        </div>
        
        <StreakAnalysisDashboard />
      </div>
    </div>
  );
};

export default StreakAnalysisPage;
