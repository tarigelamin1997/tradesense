
import React from 'react';
import FeatureVotingBoard from '../components/FeatureVotingBoard';

const FeatureVotingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8">
        <FeatureVotingBoard />
      </div>
    </div>
  );
};

export default FeatureVotingPage;
