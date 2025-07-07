
import React, { useState, useEffect } from 'react';
import { Card } from '../../../components/ui/Card';
import { playbooksApi } from '../../../services/playbooks';

interface PlaybookOptimization {
  playbook_id: string;
  playbook_name: string;
  total_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_pnl: number;
  avg_win: number;
  avg_loss: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  profit_factor: number;
  risk_reward_ratio: number;
  max_win_streak: number;
  max_loss_streak: number;
  confidence_analysis: {
    trend: string;
    correlation: number;
    avg_confidence: number;
    confidence_range: number[];
  };
  time_analysis: {
    day_performance: Record<string, any>;
    hour_performance: Record<string, any>;
    best_day: string;
    best_hour: number;
  };
  recommendation: {
    action: string;
    message: string;
    priority: string;
  };
  performance_score: number;
  created_at: string;
  last_trade_date: string;
}

interface OptimizationSummary {
  total_playbooks_analyzed: number;
  total_trades_analyzed: number;
  avg_performance_score: number;
  top_performer: string;
  high_priority_actions: number;
}

interface OptimizationData {
  summary: OptimizationSummary;
  playbooks: PlaybookOptimization[];
  generated_at: string;
}

export const PlaybookOptimizationDashboard: React.FC = () => {
  const [optimizationData, setOptimizationData] = useState<OptimizationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlaybook, setSelectedPlaybook] = useState<PlaybookOptimization | null>(null);
  const [sortBy, setSortBy] = useState<'performance_score' | 'total_pnl' | 'win_rate' | 'sharpe_ratio'>('performance_score');

  useEffect(() => {
    fetchOptimizationData();
  }, []);

  const fetchOptimizationData = async () => {
    try {
      setLoading(true);
      const data = await playbooksApi.getOptimizationSummary();
      setOptimizationData(data);
    } catch (err) {
      setError('Failed to load optimization data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getRecommendationColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getPerformanceScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const sortedPlaybooks = optimizationData?.playbooks.sort((a, b) => {
    switch (sortBy) {
      case 'performance_score': return b.performance_score - a.performance_score;
      case 'total_pnl': return b.total_pnl - a.total_pnl;
      case 'win_rate': return b.win_rate - a.win_rate;
      case 'sharpe_ratio': return b.sharpe_ratio - a.sharpe_ratio;
      default: return b.performance_score - a.performance_score;
    }
  }) || [];

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error || !optimizationData) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {error || 'Failed to load optimization data'}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          🎯 Playbook Optimization Engine
        </h1>
        <p className="text-gray-600">
          Data-driven insights to optimize your trading strategies
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {optimizationData.summary.total_playbooks_analyzed}
            </div>
            <div className="text-sm text-gray-600">Playbooks Analyzed</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {optimizationData.summary.total_trades_analyzed}
            </div>
            <div className="text-sm text-gray-600">Total Trades</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {optimizationData.summary.avg_performance_score.toFixed(1)}
            </div>
            <div className="text-sm text-gray-600">Avg Performance Score</div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {optimizationData.summary.high_priority_actions}
            </div>
            <div className="text-sm text-gray-600">High Priority Actions</div>
          </div>
        </Card>
      </div>

      {/* Top Performer Highlight */}
      {optimizationData.summary.top_performer && (
        <Card className="p-6 bg-gradient-to-r from-green-50 to-blue-50 border-l-4 border-green-500">
          <div className="flex items-center">
            <div className="text-2xl mr-3">🏆</div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Top Performer: {optimizationData.summary.top_performer}
              </h3>
              <p className="text-gray-600">
                Your most successful strategy based on comprehensive performance metrics
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Sort Controls */}
      <div className="flex items-center space-x-4">
        <label className="text-sm font-medium text-gray-700">Sort by:</label>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as any)}
          className="border border-gray-300 rounded-md px-3 py-1 text-sm"
        >
          <option value="performance_score">Performance Score</option>
          <option value="total_pnl">Total P&L</option>
          <option value="win_rate">Win Rate</option>
          <option value="sharpe_ratio">Sharpe Ratio</option>
        </select>
      </div>

      {/* Playbooks Table */}
      <Card className="overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Playbook Performance Analysis
          </h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Playbook
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Score
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trades
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Win Rate
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total P&L
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sharpe
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Max DD
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Recommendation
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedPlaybooks.map((playbook, index) => (
                <tr key={playbook.playbook_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {playbook.playbook_name}
                      </div>
                      <div className="text-xs text-gray-500">
                        Created: {new Date(playbook.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPerformanceScoreColor(playbook.performance_score)}`}>
                      {playbook.performance_score}
                    </span>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {playbook.total_trades}
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`text-sm font-medium ${
                      playbook.win_rate >= 60 ? 'text-green-600' :
                      playbook.win_rate >= 40 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {playbook.win_rate.toFixed(1)}%
                    </span>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`text-sm font-medium ${
                      playbook.total_pnl > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(playbook.total_pnl)}
                    </span>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                    {playbook.sharpe_ratio.toFixed(2)}
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-red-600">
                    {formatCurrency(playbook.max_drawdown)}
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${getRecommendationColor(playbook.recommendation.priority)}`}>
                      {playbook.recommendation.action.replace(/_/g, ' ').toUpperCase()}
                    </span>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <button
                      onClick={() => setSelectedPlaybook(playbook)}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Detailed Analysis Modal */}
      {selectedPlaybook && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">
                  {selectedPlaybook.playbook_name} - Detailed Analysis
                </h2>
                <button
                  onClick={() => setSelectedPlaybook(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                {/* Core Metrics */}
                <Card className="p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">Core Metrics</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Performance Score:</span>
                      <span className="font-medium">{selectedPlaybook.performance_score}/100</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total Trades:</span>
                      <span className="font-medium">{selectedPlaybook.total_trades}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Win Rate:</span>
                      <span className="font-medium">{selectedPlaybook.win_rate.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Avg P&L:</span>
                      <span className="font-medium">{formatCurrency(selectedPlaybook.avg_pnl)}</span>
                    </div>
                  </div>
                </Card>

                {/* Risk Metrics */}
                <Card className="p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">Risk Metrics</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Sharpe Ratio:</span>
                      <span className="font-medium">{selectedPlaybook.sharpe_ratio.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Sortino Ratio:</span>
                      <span className="font-medium">{selectedPlaybook.sortino_ratio.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Max Drawdown:</span>
                      <span className="font-medium text-red-600">{formatCurrency(selectedPlaybook.max_drawdown)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Profit Factor:</span>
                      <span className="font-medium">{selectedPlaybook.profit_factor.toFixed(2)}</span>
                    </div>
                  </div>
                </Card>

                {/* Confidence Analysis */}
                <Card className="p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">Confidence Analysis</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Trend:</span>
                      <span className="font-medium capitalize">
                        {selectedPlaybook.confidence_analysis.trend.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Correlation:</span>
                      <span className="font-medium">{selectedPlaybook.confidence_analysis.correlation.toFixed(3)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Avg Confidence:</span>
                      <span className="font-medium">{selectedPlaybook.confidence_analysis.avg_confidence.toFixed(1)}/10</span>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Time Analysis */}
              <Card className="p-4 mb-6">
                <h4 className="font-semibold text-gray-900 mb-3">Optimal Trading Times</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h5 className="font-medium text-gray-700 mb-2">Best Day:</h5>
                    <p className="text-lg font-semibold text-green-600">
                      {selectedPlaybook.time_analysis.best_day}
                    </p>
                  </div>
                  <div>
                    <h5 className="font-medium text-gray-700 mb-2">Best Hour:</h5>
                    <p className="text-lg font-semibold text-green-600">
                      {selectedPlaybook.time_analysis.best_hour}:00
                    </p>
                  </div>
                </div>
              </Card>

              {/* Recommendation */}
              <Card className={`p-4 border-l-4 ${
                selectedPlaybook.recommendation.priority === 'high' ? 'border-red-500 bg-red-50' :
                selectedPlaybook.recommendation.priority === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                'border-green-500 bg-green-50'
              }`}>
                <h4 className="font-semibold text-gray-900 mb-2">
                  Recommendation ({selectedPlaybook.recommendation.priority.toUpperCase()} Priority)
                </h4>
                <p className="text-gray-700">{selectedPlaybook.recommendation.message}</p>
              </Card>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PlaybookOptimizationDashboard;
