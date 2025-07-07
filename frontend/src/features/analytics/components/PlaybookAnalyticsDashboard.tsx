
import React, { useState, useEffect } from 'react';
import { playbooksService, PlaybookAnalytics } from '../../../services/playbooks';

export const PlaybookAnalyticsDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<PlaybookAnalytics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [minTrades, setMinTrades] = useState(5);
  const [includeArchived, setIncludeArchived] = useState(false);

  useEffect(() => {
    loadAnalytics();
  }, [minTrades, includeArchived]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const data = await playbooksService.getPlaybookAnalytics({
        min_trades: minTrades,
        include_archived: includeArchived
      });
      setAnalytics(data);
    } catch (err) {
      setError('Failed to load playbook analytics');
      console.error('Error loading playbook analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'focus_more': return 'bg-green-100 text-green-800';
      case 'keep_current': return 'bg-blue-100 text-blue-800';
      case 'reduce_size': return 'bg-yellow-100 text-yellow-800';
      case 'cut_play': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getRecommendationText = (recommendation: string) => {
    switch (recommendation) {
      case 'focus_more': return '📈 Focus More';
      case 'keep_current': return '✅ Keep Current';
      case 'reduce_size': return '⚠️ Reduce Size';
      case 'cut_play': return '❌ Cut Play';
      case 'insufficient_data': return '📊 Need More Data';
      default: return recommendation;
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return '📈';
      case 'declining': return '📉';
      case 'stable': return '➡️';
      default: return '❓';
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatTime = (minutes: number) => {
    if (minutes < 60) {
      return `${Math.round(minutes)}m`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = Math.round(minutes % 60);
    return `${hours}h ${remainingMinutes}m`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Playbook Performance Analytics</h2>
        <button
          onClick={loadAnalytics}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Refresh Data
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Minimum Trades
          </label>
          <input
            type="number"
            min="1"
            value={minTrades}
            onChange={(e) => setMinTrades(parseInt(e.target.value))}
            className="border border-gray-300 rounded-md px-3 py-2 w-24"
          />
        </div>
        <div className="flex items-center">
          <input
            type="checkbox"
            id="includeArchived"
            checked={includeArchived}
            onChange={(e) => setIncludeArchived(e.target.checked)}
            className="mr-2"
          />
          <label htmlFor="includeArchived" className="text-sm text-gray-700">
            Include Archived Playbooks
          </label>
        </div>
      </div>

      {/* Summary Cards */}
      {analytics.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Total Playbooks</h3>
            <p className="text-2xl font-bold text-gray-900">{analytics.length}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Profitable Playbooks</h3>
            <p className="text-2xl font-bold text-green-600">
              {analytics.filter(p => p.total_pnl > 0).length}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Best Win Rate</h3>
            <p className="text-2xl font-bold text-blue-600">
              {Math.max(...analytics.map(p => p.win_rate), 0) * 100}%
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Total Trades</h3>
            <p className="text-2xl font-bold text-gray-900">
              {analytics.reduce((sum, p) => sum + p.total_trades, 0)}
            </p>
          </div>
        </div>
      )}

      {/* Analytics Table */}
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Playbook
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Trades
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Win Rate
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Avg P&L
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total P&L
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Avg Hold Time
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Streaks
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Trend
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Recommendation
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {analytics.map((playbook) => (
              <tr key={playbook.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{playbook.name}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {playbook.total_trades}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={`font-medium ${
                    playbook.win_rate >= 0.6 ? 'text-green-600' :
                    playbook.win_rate >= 0.4 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {(playbook.win_rate * 100).toFixed(1)}%
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={`font-medium ${
                    playbook.avg_pnl > 0 ? 'text-green-600' : 
                    playbook.avg_pnl < 0 ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {formatCurrency(playbook.avg_pnl)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={`font-bold ${
                    playbook.total_pnl > 0 ? 'text-green-600' : 
                    playbook.total_pnl < 0 ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {formatCurrency(playbook.total_pnl)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {playbook.avg_hold_time_minutes ? formatTime(playbook.avg_hold_time_minutes) : 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <div className="text-xs">
                    <div className="text-green-600">W: {playbook.consecutive_wins}</div>
                    <div className="text-red-600">L: {playbook.consecutive_losses}</div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <span title={playbook.performance_trend}>
                    {getTrendIcon(playbook.performance_trend)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    getRecommendationColor(playbook.recommendation)
                  }`}>
                    {getRecommendationText(playbook.recommendation)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {analytics.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No playbook analytics available</p>
          <p className="text-gray-400">
            Create playbooks and attach them to trades to see performance analytics
          </p>
        </div>
      )}

      {/* Insights Panel */}
      {analytics.length > 0 && (
        <div className="mt-6 bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Key Insights</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {analytics.filter(p => p.recommendation === 'focus_more').length > 0 && (
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-medium text-green-800 mb-2">📈 Focus More On:</h4>
                <ul className="text-sm text-green-700">
                  {analytics
                    .filter(p => p.recommendation === 'focus_more')
                    .slice(0, 3)
                    .map(p => (
                      <li key={p.id}>• {p.name} ({formatCurrency(p.total_pnl)})</li>
                    ))}
                </ul>
              </div>
            )}
            
            {analytics.filter(p => p.recommendation === 'cut_play').length > 0 && (
              <div className="bg-red-50 p-4 rounded-lg">
                <h4 className="font-medium text-red-800 mb-2">❌ Consider Cutting:</h4>
                <ul className="text-sm text-red-700">
                  {analytics
                    .filter(p => p.recommendation === 'cut_play')
                    .slice(0, 3)
                    .map(p => (
                      <li key={p.id}>• {p.name} ({formatCurrency(p.total_pnl)})</li>
                    ))}
                </ul>
              </div>
            )}
            
            {analytics.filter(p => p.performance_trend === 'improving').length > 0 && (
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-blue-800 mb-2">📈 Improving Trend:</h4>
                <ul className="text-sm text-blue-700">
                  {analytics
                    .filter(p => p.performance_trend === 'improving')
                    .slice(0, 3)
                    .map(p => (
                      <li key={p.id}>• {p.name}</li>
                    ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
import React, { useState, useEffect } from 'react';
import { playbooksApi, PlaybookAnalytics, PlaybookPerformance } from '../../../services/playbooks';

const PlaybookAnalyticsDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<PlaybookAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<number | undefined>(undefined);

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const data = await playbooksApi.getPlaybookAnalytics(timeRange);
      setAnalytics(data);
    } catch (err) {
      setError('Failed to load playbook analytics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getPerformanceColor = (pnl: number) => {
    if (pnl > 0) return 'text-green-600';
    if (pnl < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getRecommendation = (playbook: PlaybookPerformance) => {
    if (playbook.trade_count < 10) return { type: 'info', message: 'Need more data' };
    if (playbook.win_rate >= 60 && playbook.total_pnl > 0) return { type: 'success', message: '✅ Keep & Scale' };
    if (playbook.win_rate < 40 || playbook.total_pnl < -500) return { type: 'danger', message: '❌ Consider Cutting' };
    return { type: 'warning', message: '⚠️ Monitor Closely' };
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {error || 'Failed to load analytics'}
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">📊 Playbook Analytics</h1>
          <select
            value={timeRange || ''}
            onChange={(e) => setTimeRange(e.target.value ? parseInt(e.target.value) : undefined)}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All time</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="365">Last year</option>
          </select>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{analytics.summary.total_playbooks}</div>
            <div className="text-sm text-gray-600">Total Playbooks</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{analytics.summary.total_trades}</div>
            <div className="text-sm text-gray-600">Total Trades</div>
          </div>
          <div className={`p-4 rounded-lg ${analytics.summary.total_pnl >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
            <div className={`text-2xl font-bold ${analytics.summary.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(analytics.summary.total_pnl)}
            </div>
            <div className="text-sm text-gray-600">Total P&L</div>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="text-lg font-bold text-purple-600">
              {analytics.summary.best_performing || 'N/A'}
            </div>
            <div className="text-sm text-gray-600">Best Performing</div>
          </div>
        </div>

        {/* Playbook Performance Table */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-gray-200">
            <thead>
              <tr className="bg-gray-50">
                <th className="border border-gray-200 px-4 py-3 text-left font-semibold">Playbook</th>
                <th className="border border-gray-200 px-4 py-3 text-center font-semibold">Trades</th>
                <th className="border border-gray-200 px-4 py-3 text-center font-semibold">Total P&L</th>
                <th className="border border-gray-200 px-4 py-3 text-center font-semibold">Avg P&L</th>
                <th className="border border-gray-200 px-4 py-3 text-center font-semibold">Win Rate</th>
                <th className="border border-gray-200 px-4 py-3 text-center font-semibold">Avg Win</th>
                <th className="border border-gray-200 px-4 py-3 text-center font-semibold">Avg Loss</th>
                <th className="border border-gray-200 px-4 py-3 text-center font-semibold">Profit Factor</th>
                <th className="border border-gray-200 px-4 py-3 text-center font-semibold">Recommendation</th>
              </tr>
            </thead>
            <tbody>
              {analytics.playbooks
                .sort((a, b) => b.total_pnl - a.total_pnl)
                .map((playbook) => {
                  const recommendation = getRecommendation(playbook);
                  return (
                    <tr key={playbook.playbook_id} className="hover:bg-gray-50">
                      <td className="border border-gray-200 px-4 py-3">
                        <div className="font-medium">{playbook.playbook_name}</div>
                        {playbook.avg_hold_time_minutes && (
                          <div className="text-sm text-gray-500">
                            Avg Hold: {Math.round(playbook.avg_hold_time_minutes)}min
                          </div>
                        )}
                      </td>
                      <td className="border border-gray-200 px-4 py-3 text-center">{playbook.trade_count}</td>
                      <td className={`border border-gray-200 px-4 py-3 text-center font-medium ${getPerformanceColor(playbook.total_pnl)}`}>
                        {formatCurrency(playbook.total_pnl)}
                      </td>
                      <td className={`border border-gray-200 px-4 py-3 text-center ${getPerformanceColor(playbook.avg_pnl)}`}>
                        {formatCurrency(playbook.avg_pnl)}
                      </td>
                      <td className="border border-gray-200 px-4 py-3 text-center">{formatPercentage(playbook.win_rate)}</td>
                      <td className="border border-gray-200 px-4 py-3 text-center text-green-600">
                        {formatCurrency(playbook.avg_win)}
                      </td>
                      <td className="border border-gray-200 px-4 py-3 text-center text-red-600">
                        {formatCurrency(playbook.avg_loss)}
                      </td>
                      <td className="border border-gray-200 px-4 py-3 text-center">
                        {playbook.profit_factor ? playbook.profit_factor.toFixed(2) : 'N/A'}
                      </td>
                      <td className="border border-gray-200 px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          recommendation.type === 'success' ? 'bg-green-100 text-green-800' :
                          recommendation.type === 'danger' ? 'bg-red-100 text-red-800' :
                          recommendation.type === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {recommendation.message}
                        </span>
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>

        {analytics.playbooks.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No playbook data</h3>
            <p className="text-gray-600">
              Create playbooks and attach them to trades to see analytics
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PlaybookAnalyticsDashboard;
