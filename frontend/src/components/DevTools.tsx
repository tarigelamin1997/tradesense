import React, { useState, useEffect } from 'react';
import { performanceMonitor } from '../utils/performance';

interface DevToolsProps {
  isOpen: boolean;
  onToggle: () => void;
}

export const DevTools: React.FC<DevToolsProps> = ({ isOpen, onToggle }) => {
  const [metrics, setMetrics] = useState(performanceMonitor.getMetrics());
  const [selectedTab, setSelectedTab] = useState<'performance' | 'network' | 'store'>('performance');

  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(performanceMonitor.getMetrics());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  if (!isOpen || process.env.NODE_ENV !== 'development') {
    return null;
  }

  const renderPerformanceTab = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-800">Performance Metrics</h3>
      <div className="grid grid-cols-2 gap-4">
        {metrics.slice(-10).map((metric, index) => (
          <div key={index} className="bg-gray-50 p-3 rounded-lg">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">{metric.name}</span>
              <span className={`px-2 py-1 rounded text-xs ${
                metric.rating === 'good' ? 'bg-green-100 text-green-800' :
                metric.rating === 'needs-improvement' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {metric.rating}
              </span>
            </div>
            <div className="text-xl font-bold text-gray-900">
              {metric.value.toFixed(2)}ms
            </div>
            <div className="text-xs text-gray-500">
              {new Date(metric.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderNetworkTab = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-800">Network Performance</h3>
      <div className="bg-gray-50 p-4 rounded-lg">
        <p className="text-sm text-gray-600">
          Network monitoring will be available when connected to backend API
        </p>
      </div>
    </div>
  );

  const renderStoreTab = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-800">State Management</h3>
      <div className="bg-gray-50 p-4 rounded-lg">
        <p className="text-sm text-gray-600">
          Redux DevTools integration available in browser extension
        </p>
      </div>
    </div>
  );

  return (
    <div className="fixed bottom-4 right-4 w-96 max-h-96 bg-white border border-gray-300 rounded-lg shadow-lg z-50 overflow-hidden">
      <div className="bg-gray-100 px-4 py-2 flex justify-between items-center">
        <h2 className="text-sm font-semibold text-gray-800">🛠️ Dev Tools</h2>
        <button
          onClick={onToggle}
          className="text-gray-500 hover:text-gray-700 text-lg"
        >
          ×
        </button>
      </div>

      <div className="flex border-b border-gray-200">
        {(['performance', 'network', 'store'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            className={`px-4 py-2 text-sm capitalize ${
              selectedTab === tab
                ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="p-4 overflow-y-auto max-h-80">
        {selectedTab === 'performance' && renderPerformanceTab()}
        {selectedTab === 'network' && renderNetworkTab()}
        {selectedTab === 'store' && renderStoreTab()}
      </div>
    </div>
  );
};

// Global DevTools Toggle
export const DevToolsToggle: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-4 left-4 bg-blue-600 text-white p-3 rounded-full shadow-lg hover:bg-blue-700 z-40"
        title="Toggle Dev Tools"
      >
        🛠️
      </button>
      <DevTools isOpen={isOpen} onToggle={() => setIsOpen(!isOpen)} />
    </>
  );
};