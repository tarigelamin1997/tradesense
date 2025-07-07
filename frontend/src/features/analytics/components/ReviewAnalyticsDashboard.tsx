
import React, { useState, useEffect } from 'react';
import { reviewsService, ReviewInsights, formatMistakeTag, formatMoodTag } from '../../../services/reviews';

export const ReviewAnalyticsDashboard: React.FC = () => {
  const [insights, setInsights] = useState<ReviewInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState(30);

  useEffect(() => {
    loadInsights();
  }, [timeframe]);

  const loadInsights = async () => {
    try {
      setLoading(true);
      const data = await reviewsService.getReviewInsights(timeframe);
      setInsights(data);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load review insights');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-600">{error}</p>
        <button
          onClick={loadInsights}
          className="mt-2 text-sm text-red-600 underline hover:text-red-800"
        >
          Try again
        </button>
      </div>
    );
  }

  if (!insights || insights.patterns.total_reviews === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 text-lg mb-4">📝</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Review Data</h3>
        <p className="text-gray-500">Start reviewing your trades to see insights here.</p>
      </div>
    );
  }

  const { patterns, recommendations, warnings, achievements } = insights;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Review Analytics</h2>
        <select
          value={timeframe}
          onChange={(e) => setTimeframe(parseInt(e.target.value))}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
          <option value={365}>Last year</option>
        </select>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{patterns.total_reviews}</div>
            <div className="text-sm text-gray-500">Total Reviews</div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-center">
            <div className={`text-3xl font-bold ${patterns.avg_quality_score >= 4 ? 'text-green-600' : patterns.avg_quality_score >= 3 ? 'text-yellow-600' : 'text-red-600'}`}>
              {patterns.avg_quality_score.toFixed(1)}/5
            </div>
            <div className="text-sm text-gray-500">Avg Quality Score</div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600">
              {patterns.improvement_areas.length}
            </div>
            <div className="text-sm text-gray-500">Focus Areas</div>
          </div>
        </div>
      </div>

      {/* Insights Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Achievements */}
        {achievements.length > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-800 mb-4 flex items-center">
              🏆 Achievements
            </h3>
            <ul className="space-y-2">
              {achievements.map((achievement, index) => (
                <li key={index} className="text-green-700 flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  {achievement}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Warnings */}
        {warnings.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-red-800 mb-4 flex items-center">
              ⚠️ Warnings
            </h3>
            <ul className="space-y-2">
              {warnings.map((warning, index) => (
                <li key={index} className="text-red-700 flex items-start">
                  <span className="text-red-500 mr-2">!</span>
                  {warning}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 lg:col-span-2">
            <h3 className="text-lg font-semibold text-blue-800 mb-4 flex items-center">
              💡 Recommendations
            </h3>
            <ul className="space-y-2">
              {recommendations.map((recommendation, index) => (
                <li key={index} className="text-blue-700 flex items-start">
                  <span className="text-blue-500 mr-2">→</span>
                  {recommendation}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Detailed Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Most Common Mistakes */}
        {patterns.most_common_mistakes.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Most Common Mistakes</h3>
            <div className="space-y-3">
              {patterns.most_common_mistakes.slice(0, 5).map((mistake, index) => (
                <div key={mistake.mistake} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">{formatMistakeTag(mistake.mistake)}</span>
                  <div className="flex items-center space-x-2">
                    <div className="bg-gray-200 rounded-full h-2 w-20">
                      <div
                        className="bg-red-500 h-2 rounded-full"
                        style={{ width: `${mistake.percentage}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-500 w-12 text-right">
                      {mistake.percentage}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Mood Performance */}
        {patterns.mood_performance.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Mood vs Performance</h3>
            <div className="space-y-3">
              {patterns.mood_performance.slice(0, 5).map((mood, index) => (
                <div key={mood.mood} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-700">{formatMoodTag(mood.mood)}</span>
                    <span className="text-xs text-gray-400">({mood.count})</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="bg-gray-200 rounded-full h-2 w-20">
                      <div
                        className={`h-2 rounded-full ${
                          mood.avg_quality >= 4 ? 'bg-green-500' : 
                          mood.avg_quality >= 3 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${(mood.avg_quality / 5) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-700 w-8 text-right">
                      {mood.avg_quality.toFixed(1)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Quality Trend */}
      {patterns.quality_trend.length > 5 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quality Score Trend</h3>
          <div className="h-64 flex items-end justify-between space-x-1">
            {patterns.quality_trend.slice(-14).map((point, index) => (
              <div key={point.date} className="flex flex-col items-center">
                <div
                  className={`w-4 rounded-t ${
                    point.avg_quality >= 4 ? 'bg-green-500' : 
                    point.avg_quality >= 3 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ height: `${(point.avg_quality / 5) * 100}%` }}
                ></div>
                <span className="text-xs text-gray-400 mt-1 transform -rotate-45 origin-left">
                  {new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
