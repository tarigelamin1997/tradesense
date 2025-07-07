
import React from 'react';
import { PlaybookManager } from '../components/PlaybookManager';

export const PlaybookManagerPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <PlaybookManager />
    </div>
  );
};
import React from 'react';
import PlaybookManager from '../components/PlaybookManager';

const PlaybookManagerPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <PlaybookManager />
    </div>
  );
};

export default PlaybookManagerPage;
