
import React, { useState, useEffect } from 'react';
import { Bar, Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  RadialLinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

import { edgeStrengthService, EdgeStrengthAnalysis, StrategyComparisonResponse, EdgeStrengthFilters } from '../../../services/edgeStrength';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  RadialLinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const EdgeStrengthDashboard: React.FC = () => {
  const [analysis, setAnalysis] = useState<EdgeStrengthAnalysis | null>(null);
  const [comparison, setComparison] = useState<StrategyComparisonResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<EdgeStrengthFilters>({
    min_trades: 10
  });
  const [viewMode, setViewMode] = useState<'overview' | 'comparison'>('overview');

  useEffect(() => {
    loadData();
  }, [filters]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [analysisData, comparisonData] = await Promise.all([
        edgeStrengthService.getEdgeStrengthAnalysis(filters),
        edgeStrengthService.getStrategyComparison({
          start_date: filters.start_date,
          end_date: filters.end_date
        })
      ]);
      
      setAnalysis(analysisData);
      setComparison(comparisonData);
    } catch (err) {
      setError('Failed to load edge strength analysis');
      console.error('Error loading edge strength data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getEdgeStrengthBarData = () => {
    if (!analysis) return null;

    const strategies = Object.entries(analysis.strategies);
    const labels = strategies.map(([name]) => name);
    const edgeStrengths = strategies.map(([, metrics]) => metrics.edge_strength);
    const pnlData = strategies.map(([, metrics]) => metrics.total_pnl);

    return {
      labels,
      datasets: [
        {
          label: 'Edge Strength Score',
          data: edgeStrengths,
          backgroundColor: edgeStrengths.map(score => {
            if (score >= 70) return 'rgba(34, 197, 94, 0.8)';
            if (score >= 50) return 'rgba(234, 179, 8, 0.8)';
            if (score >= 30) return 'rgba(249, 115, 22, 0.8)';
            return 'rgba(239, 68, 68, 0.8)';
          }),
          borderColor: edgeStrengths.map(score => {
            if (score >= 70) return 'rgb(34, 197, 94)';
            if (score >= 50) return 'rgb(234, 179, 8)';
            if (score >= 30) return 'rgb(249, 115, 22)';
            return 'rgb(239, 68, 68)';
          }),
          borderWidth: 1,
        }
      ]
    };
  };

  const getRadarData = () => {
    if (!analysis) return null;

    const strategies = Object.entries(analysis.strategies).slice(0, 3); // Top 3 strategies
    const labels = ['Win Rate', 'Profit Factor', 'Edge Strength', 'Consistency', 'Sample Size'];

    const datasets = strategies.map(([name, metrics], index) => ({
      label: name,
      data: [
        metrics.win_rate,
        Math.min(metrics.profit_factor * 20, 100), // Normalize profit factor
        metrics.edge_strength,
        metrics.consistency_score,
        Math.min(metrics.total_trades / 50 * 100, 100) // Normalize sample size
      ],
      backgroundColor: `hsla(${index * 120}, 70%, 50%, 0.2)`,
      borderColor: `hsla(${index * 120}, 70%, 50%, 1)`,
      borderWidth: 2,
    }));

    return { labels, datasets };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Edge Analysis</h3>
        <p className="text-red-600">{error}</p>
        <button
          onClick={loadData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!analysis || Object.keys(analysis.strategies).length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">No Strategy Data Available</h3>
        <p className="text-gray-600 mb-4">
          Start tagging your trades with strategy names to see edge strength analysis.
        </p>
        <div className="text-sm text-gray-500">
          <p>Tips:</p>
          <ul className="list-disc list-inside mt-2">
            <li>Tag trades with strategies like "breakout", "pullback", "reversal"</li>
            <li>Need at least {filters.min_trades} trades per strategy for analysis</li>
            <li>Be consistent with your strategy naming</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">📊 Strategy Edge Strength</h2>
          <p className="text-gray-600">Discover which strategies are truly profitable</p>
        </div>
        
        <div className="flex space-x-4">
          <select
            value={viewMode}
            onChange={(e) => setViewMode(e.target.value as 'overview' | 'comparison')}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="overview">Overview</option>
            <option value="comparison">Comparison</option>
          </select>
          
          <select
            value={filters.min_trades}
            onChange={(e) => setFilters({...filters, min_trades: parseInt(e.target.value)})}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value={5}>Min 5 trades</option>
            <option value={10}>Min 10 trades</option>
            <option value={20}>Min 20 trades</option>
            <option value={30}>Min 30 trades</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Strategies</h3>
          <p className="text-2xl font-bold text-gray-900">{analysis.summary.total_strategies}</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Profitable Strategies</h3>
          <p className="text-2xl font-bold text-green-600">{analysis.summary.profitable_strategies}</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Strong Edge (70%+)</h3>
          <p className="text-2xl font-bold text-blue-600">{analysis.summary.strong_edge_strategies}</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Best Strategy</h3>
          <p className="text-lg font-bold text-gray-900">
            {analysis.summary.best_strategy || 'N/A'}
          </p>
        </div>
      </div>

      {viewMode === 'overview' ? (
        <>
          {/* Edge Strength Chart */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Edge Strength by Strategy</h3>
            <div className="h-64">
              <Bar
                data={getEdgeStrengthBarData()!}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      display: false
                    },
                    tooltip: {
                      callbacks: {
                        afterLabel: (context) => {
                          const strategyName = context.label;
                          const metrics = analysis.strategies[strategyName];
                          return [
                            `Total P&L: $${metrics.total_pnl.toFixed(2)}`,
                            `Win Rate: ${metrics.win_rate}%`,
                            `Trades: ${metrics.total_trades}`
                          ];
                        }
                      }
                    }
                  },
                  scales: {
                    y: {
                      beginAtZero: true,
                      max: 100,
                      title: {
                        display: true,
                        text: 'Edge Strength Score'
                      }
                    }
                  }
                }}
              />
            </div>
          </div>

          {/* Strategy Details Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold">Strategy Performance Details</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Strategy</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Edge Score</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Win Rate</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Profit Factor</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total P&L</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trades</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recommendation</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.entries(analysis.strategies)
                    .sort(([,a], [,b]) => b.edge_strength - a.edge_strength)
                    .map(([name, metrics]) => (
                    <tr key={name}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${edgeStrengthService.getEdgeStrengthBadgeColor(metrics.edge_strength)}`}>
                          {metrics.edge_strength.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {metrics.win_rate.toFixed(1)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {metrics.profit_factor === 999 ? '∞' : metrics.profit_factor.toFixed(2)}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${metrics.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${metrics.total_pnl.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {metrics.total_trades}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`font-medium ${edgeStrengthService.getRecommendationColor(getRecommendation(metrics))}`}>
                          {getRecommendation(metrics)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <>
          {/* Radar Chart Comparison */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Strategy Comparison (Top 3)</h3>
            <div className="h-64">
              <Radar
                data={getRadarData()!}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'top',
                    }
                  },
                  scales: {
                    r: {
                      beginAtZero: true,
                      max: 100,
                    }
                  }
                }}
              />
            </div>
          </div>

          {/* Insights */}
          {comparison && comparison.insights.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-3">📈 Key Insights</h3>
              <ul className="space-y-2">
                {comparison.insights.map((insight, index) => (
                  <li key={index} className="text-blue-800">{insight}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
};

const getRecommendation = (metrics: any): string => {
  if (metrics.total_trades < 10) return "Need more data";
  if (metrics.edge_strength >= 70) return "Scale up";
  if (metrics.edge_strength >= 50) return "Monitor closely";
  if (metrics.edge_strength >= 30) return "Needs improvement";
  return "Consider stopping";
};

export default EdgeStrengthDashboard;
