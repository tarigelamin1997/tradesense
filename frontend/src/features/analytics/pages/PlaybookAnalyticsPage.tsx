
import React from 'react';
import { PlaybookAnalyticsDashboard } from '../components/PlaybookAnalyticsDashboard';

export const PlaybookAnalyticsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <PlaybookAnalyticsDashboard />
    </div>
  );
};
import React from 'react';
import PlaybookAnalyticsDashboard from '../components/PlaybookAnalyticsDashboard';

const PlaybookAnalyticsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <PlaybookAnalyticsDashboard />
    </div>
  );
};

export default PlaybookAnalyticsPage;
