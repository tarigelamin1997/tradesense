
import React, { useState, useEffect } from 'react';
import { PlaybookComparisonDashboard } from '../components/PlaybookComparisonDashboard';
import { playbooksService } from '../../../services/playbooks';

interface Playbook {
  id: string;
  name: string;
  description?: string;
  total_trades: number;
}

export const PlaybookComparisonPage: React.FC = () => {
  const [availablePlaybooks, setAvailablePlaybooks] = useState<Playbook[]>([]);
  const [selectedPlaybooks, setSelectedPlaybooks] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPlaybooks();
  }, []);

  const loadPlaybooks = async () => {
    setLoading(true);
    try {
      const response = await playbooksService.getPlaybooks();
      setAvailablePlaybooks(response.playbooks || []);
    } catch (error) {
      console.error('Error loading playbooks:', error);
    } finally {
      setLoading(false);
    }
  };

  const togglePlaybookSelection = (playbookId: string) => {
    setSelectedPlaybooks(prev => 
      prev.includes(playbookId) 
        ? prev.filter(id => id !== playbookId)
        : [...prev, playbookId]
    );
  };

  const selectAllPlaybooks = () => {
    setSelectedPlaybooks(availablePlaybooks.map(p => p.id));
  };

  const clearSelection = () => {
    setSelectedPlaybooks([]);
  };

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading playbooks...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Select Playbooks to Compare</h2>
          <div className="flex gap-2">
            <button
              onClick={selectAllPlaybooks}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Select All
            </button>
            <button
              onClick={clearSelection}
              className="px-4 py-2 text-sm bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              Clear All
            </button>
          </div>
        </div>

        {availablePlaybooks.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-6xl mb-4">📚</div>
            <h3 className="text-xl font-semibold mb-2 text-gray-900">No Playbooks Found</h3>
            <p className="text-gray-600">Create some playbooks first to start comparing performance.</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {availablePlaybooks.map((playbook) => (
                <div 
                  key={playbook.id}
                  className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                    selectedPlaybooks.includes(playbook.id)
                      ? 'border-blue-500 bg-blue-50 shadow-md'
                      : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                  }`}
                  onClick={() => togglePlaybookSelection(playbook.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg text-gray-900 mb-1">
                        {playbook.name}
                      </h3>
                      {playbook.description && (
                        <p className="text-gray-600 text-sm mb-2">{playbook.description}</p>
                      )}
                      <p className="text-sm text-gray-500">
                        {playbook.total_trades} trades
                      </p>
                    </div>
                    <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                      selectedPlaybooks.includes(playbook.id)
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-gray-300'
                    }`}>
                      {selectedPlaybooks.includes(playbook.id) && (
                        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between bg-gray-50 rounded-lg p-4">
              <div>
                <p className="text-sm text-gray-600">
                  {selectedPlaybooks.length} of {availablePlaybooks.length} playbooks selected
                </p>
                {selectedPlaybooks.length >= 2 && (
                  <p className="text-sm text-green-600 font-medium">
                    ✓ Ready to compare!
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                {selectedPlaybooks.length >= 2 && (
                  <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                    Comparison Ready
                  </span>
                )}
                {selectedPlaybooks.length > 5 && (
                  <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                    Many playbooks selected
                  </span>
                )}
              </div>
            </div>
          </>
        )}
      </div>

      <PlaybookComparisonDashboard selectedPlaybooks={selectedPlaybooks} />
    </div>
  );
};
