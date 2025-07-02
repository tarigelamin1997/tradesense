
import React, { useState, useEffect } from 'react';
import { edgeStrengthService, RecommendationsResponse } from '../../../services/edgeStrength';

const StrategyRecommendations: React.FC = () => {
  const [recommendations, setRecommendations] = useState<RecommendationsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadRecommendations();
  }, []);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await edgeStrengthService.getRecommendations();
      setRecommendations(data);
    } catch (err) {
      setError('Failed to load recommendations');
      console.error('Error loading recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !recommendations) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-red-600 mb-2">Error</h3>
        <p className="text-gray-600">{error}</p>
        <button
          onClick={loadRecommendations}
          className="mt-2 text-blue-600 hover:text-blue-800 text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">🎯 Strategy Recommendations</h3>
        <p className="text-sm text-gray-600">{recommendations.summary}</p>
      </div>
      
      <div className="p-6">
        {/* Action Items */}
        {recommendations.action_items.length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Immediate Actions</h4>
            <ul className="space-y-2">
              {recommendations.action_items.map((item, index) => (
                <li key={index} className="flex items-start space-x-2">
                  <span className="text-blue-500 mt-1">•</span>
                  <span className="text-sm text-gray-700">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Detailed Recommendations */}
        {recommendations.recommendations.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-3">Detailed Analysis</h4>
            <div className="space-y-4">
              {recommendations.recommendations.map((rec, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border-l-4 ${
                    rec.priority === 'high'
                      ? 'bg-red-50 border-red-400'
                      : rec.priority === 'medium'
                      ? 'bg-yellow-50 border-yellow-400'
                      : 'bg-green-50 border-green-400'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h5 className="font-medium text-gray-900">{rec.strategy}</h5>
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded ${
                        rec.priority === 'high'
                          ? 'bg-red-100 text-red-800'
                          : rec.priority === 'medium'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-green-100 text-green-800'
                      }`}
                    >
                      {rec.priority} priority
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 mb-1">{rec.message}</p>
                  <p className="text-xs text-gray-500">{rec.target}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {recommendations.recommendations.length === 0 && recommendations.action_items.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">No specific recommendations available.</p>
            <p className="text-sm text-gray-400 mt-2">
              Keep trading and tagging your strategies to get personalized insights.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default StrategyRecommendations;
