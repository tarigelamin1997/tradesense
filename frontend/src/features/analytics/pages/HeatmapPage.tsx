
import React, { useState } from 'react';
import PerformanceHeatmap from '../components/PerformanceHeatmap';

const HeatmapPage: React.FC = () => {
  const [dateRange, setDateRange] = useState<{
    startDate: string;
    endDate: string;
  }>({
    startDate: '',
    endDate: ''
  });

  const handleDateRangeChange = (field: 'startDate' | 'endDate', value: string) => {
    setDateRange(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const clearDateRange = () => {
    setDateRange({
      startDate: '',
      endDate: ''
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Performance Heatmap</h1>
              <p className="mt-2 text-lg text-gray-600">
                Discover your optimal trading times and best-performing symbols
              </p>
            </div>
            
            {/* Date Range Controls */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">From:</label>
                <input
                  type="date"
                  value={dateRange.startDate}
                  onChange={(e) => handleDateRangeChange('startDate', e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">To:</label>
                <input
                  type="date"
                  value={dateRange.endDate}
                  onChange={(e) => handleDateRangeChange('endDate', e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              {(dateRange.startDate || dateRange.endDate) && (
                <button
                  onClick={clearDateRange}
                  className="px-3 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  Clear
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Key Benefits Banner */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-lg mb-8">
          <h2 className="text-xl font-semibold mb-3">🎯 What You'll Discover</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">🕒</span>
              <div>
                <div className="font-medium">Peak Hours</div>
                <div className="text-sm opacity-90">When you perform best</div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-2xl">📈</span>
              <div>
                <div className="font-medium">Top Symbols</div>
                <div className="text-sm opacity-90">Your winning instruments</div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-2xl">⚠️</span>
              <div>
                <div className="font-medium">Risk Zones</div>
                <div className="text-sm opacity-90">Times to avoid trading</div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-2xl">💡</span>
              <div>
                <div className="font-medium">Smart Insights</div>
                <div className="text-sm opacity-90">Actionable recommendations</div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Heatmap Component */}
        <PerformanceHeatmap 
          startDate={dateRange.startDate || undefined}
          endDate={dateRange.endDate || undefined}
        />

        {/* Usage Tips */}
        <div className="mt-8 bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold mb-4">💡 How to Use This Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">🕒 Time Heatmap</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Green cells = profitable time slots</li>
                <li>• Red cells = losing time slots</li>
                <li>• Hover for detailed statistics</li>
                <li>• Focus trading on green zones</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">📈 Symbol Analysis</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Sort by any metric to find patterns</li>
                <li>• Consistency score shows reliability</li>
                <li>• Direction bias reveals preferences</li>
                <li>• Scale winning symbols up</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">💡 Recommendations</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• High priority = immediate action</li>
                <li>• Medium priority = gradual changes</li>
                <li>• Focus on expected impact</li>
                <li>• Review recommendations weekly</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HeatmapPage;
