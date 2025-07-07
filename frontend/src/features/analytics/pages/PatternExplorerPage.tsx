
import React from 'react';
import PatternExplorer from '../components/PatternExplorer';

const PatternExplorerPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <PatternExplorer />
      </div>
    </div>
  );
};

export default PatternExplorerPage;
