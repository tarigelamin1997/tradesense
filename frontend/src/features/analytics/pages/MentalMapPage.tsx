
import React, { useState } from 'react';
import { MentalMapDashboard } from '../components/MentalMapDashboard';
import { MentalMapTimeline } from '../components/MentalMapTimeline';
import { Button } from '../../../components/ui/Button';

export const MentalMapPage: React.FC = () => {
  const [currentView, setCurrentView] = useState<'dashboard' | 'timeline'>('dashboard');
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');

  const handleViewTimeline = (sessionId: string) => {
    setSelectedSessionId(sessionId);
    setCurrentView('timeline');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-semibold text-gray-900">Mental Map</h1>
              <div className="flex items-center space-x-2">
                <Button
                  onClick={() => setCurrentView('dashboard')}
                  variant={currentView === 'dashboard' ? 'default' : 'outline'}
                  size="sm"
                >
                  Dashboard
                </Button>
                {selectedSessionId && (
                  <Button
                    onClick={() => setCurrentView('timeline')}
                    variant={currentView === 'timeline' ? 'default' : 'outline'}
                    size="sm"
                  >
                    Timeline
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto">
        {currentView === 'dashboard' && (
          <MentalMapDashboard />
        )}
        
        {currentView === 'timeline' && selectedSessionId && (
          <div className="p-6">
            <MentalMapTimeline sessionId={selectedSessionId} />
          </div>
        )}
      </div>
    </div>
  );
};
