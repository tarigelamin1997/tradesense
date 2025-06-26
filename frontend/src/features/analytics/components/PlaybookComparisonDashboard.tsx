import React, { useState, useEffect } from 'react';
import { analyticsService } from '../../../services/analytics';

interface PlaybookComparison {
  playbook_name: string;
  total_trades: number;
  win_rate: number;
  avg_pnl: number;
  total_pnl: number;
  profit_factor: number;
  max_drawdown: number;
  sharpe_ratio: number;
  avg_hold_time: number;
  best_month: string;
  worst_month: string;
  consistency_score: number;
}

interface PerformanceMetric {
  date: string;
  [key: string]: string | number;
}

const PlaybookComparisonDashboard: React.FC = () => {
  const [comparisons, setComparisons] = useState<PlaybookComparison[]>([]);
  const [performanceData, setPerformanceData] = useState<PerformanceMetric[]>([]);
  const [selectedPlaybooks, setSelectedPlaybooks] = useState<string[]>([]);
  const [availablePlaybooks, setAvailablePlaybooks] = useState<string[]>([]);
  const [timeframe, setTimeframe] = useState('3M');
  const [comparisonType, setComparisonType] = useState('win_rate');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPlaybookComparisons();
    loadAvailablePlaybooks();
  }, [timeframe]);

  const loadPlaybookComparisons = async () => {
    try {
      setLoading(true);
      const data = await analyticsService.getPlaybookComparison(timeframe);
      setComparisons(data.comparisons || []);
      setPerformanceData(data.performance_timeline || []);

      // Auto-select top 3 performing playbooks
      const topPlaybooks = data.comparisons
        ?.sort((a: PlaybookComparison, b: PlaybookComparison) => b.profit_factor - a.profit_factor)
        .slice(0, 3)
        .map((p: PlaybookComparison) => p.playbook_name) || [];
      setSelectedPlaybooks(topPlaybooks);
    } catch (err) {
      setError('Failed to load playbook comparisons');
      console.error('Playbook comparison error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailablePlaybooks = async () => {
    try {
      const data = await analyticsService.getAvailablePlaybooks();
      setAvailablePlaybooks(data.playbooks || []);
    } catch (err) {
      console.error('Failed to load available playbooks:', err);
    }
  };

  const getMetricValue = (playbook: PlaybookComparison, metric: string): number => {
    switch (metric) {
      case 'win_rate': return playbook.win_rate;
      case 'avg_pnl': return playbook.avg_pnl;
      case 'profit_factor': return playbook.profit_factor;
      case 'sharpe_ratio': return playbook.sharpe_ratio;
      case 'consistency_score': return playbook.consistency_score;
      default: return 0;
    }
  };

  const getMetricLabel = (metric: string): string => {
    switch (metric) {
      case 'win_rate': return 'Win Rate (%)';
      case 'avg_pnl': return 'Avg P&L ($)';
      case 'profit_factor': return 'Profit Factor';
      case 'sharpe_ratio': return 'Sharpe Ratio';
      case 'consistency_score': return 'Consistency Score';
      default: return metric;
    }
  };

  const getMetricColor = (index: number): string => {
    const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];
    return colors[index % colors.length];
  };

  const togglePlaybookSelection = (playbook: string) => {
    setSelectedPlaybooks(prev => 
      prev.includes(playbook) 
        ? prev.filter(p => p !== playbook)
        : [...prev, playbook]
    );
  };

  const renderComparisonChart = () => {
    const selectedData = comparisons.filter(p => selectedPlaybooks.includes(p.playbook_name));
    const maxValue = Math.max(...selectedData.map(p => getMetricValue(p, comparisonType)));

    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h3 className="text-lg font-semibold mb-4">{getMetricLabel(comparisonType)} Comparison</h3>
        <div className="space-y-4">
          {selectedData.map((playbook, index) => {
            const value = getMetricValue(playbook, comparisonType);
            const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;
            const color = getMetricColor(index);

            return (
              <div key={playbook.playbook_name} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-sm">{playbook.playbook_name}</span>
                  <span className="text-sm font-semibold" style={{ color }}>
                    {comparisonType === 'win_rate' ? `${value.toFixed(1)}%` :
                     comparisonType === 'avg_pnl' ? `$${value.toFixed(2)}` :
                     value.toFixed(2)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="h-3 rounded-full transition-all duration-300"
                    style={{ 
                      width: `${Math.max(percentage, 5)}%`,
                      backgroundColor: color
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderPerformanceTimeline = () => {
    if (!performanceData.length) return null;

    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h3 className="text-lg font-semibold mb-4">Performance Timeline</h3>
        <div className="h-64 relative">
          <svg width="100%" height="100%" viewBox="0 0 800 200">
            {selectedPlaybooks.map((playbook, index) => {
              const color = getMetricColor(index);
              const playbookData = performanceData.map(d => ({
                date: d.date,
                value: d[playbook] as number || 0
              }));

              const maxValue = Math.max(...playbookData.map(d => d.value));
              const minValue = Math.min(...playbookData.map(d => d.value));
              const range = maxValue - minValue || 1;

              const pathData = playbookData.map((d, i) => {
                const x = (i / (playbookData.length - 1)) * 750 + 25;
                const y = 175 - ((d.value - minValue) / range) * 150;
                return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
              }).join(' ');

              return (
                <g key={playbook}>
                  <path
                    d={pathData}
                    fill="none"
                    stroke={color}
                    strokeWidth="2"
                    className="transition-all duration-300"
                  />
                  {playbookData.map((d, i) => {
                    const x = (i / (playbookData.length - 1)) * 750 + 25;
                    const y = 175 - ((d.value - minValue) / range) * 150;
                    return (
                      <circle
                        key={i}
                        cx={x}
                        cy={y}
                        r="3"
                        fill={color}
                        className="hover:r-5 transition-all duration-200"
                      />
                    );
                  })}
                </g>
              );
            })}
          </svg>
        </div>
        <div className="flex flex-wrap gap-4 mt-4">
          {selectedPlaybooks.map((playbook, index) => (
            <div key={playbook} className="flex items-center space-x-2">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getMetricColor(index) }}
              />
              <span className="text-sm">{playbook}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderSummaryTable = () => {
    const selectedData = comparisons.filter(p => selectedPlaybooks.includes(p.playbook_name));

    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h3 className="text-lg font-semibold mb-4">Detailed Comparison</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full table-auto">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 px-3 font-medium">Playbook</th>
                <th className="text-right py-2 px-3 font-medium">Trades</th>
                <th className="text-right py-2 px-3 font-medium">Win Rate</th>
                <th className="text-right py-2 px-3 font-medium">Avg P&L</th>
                <th className="text-right py-2 px-3 font-medium">Total P&L</th>
                <th className="text-right py-2 px-3 font-medium">Profit Factor</th>
                <th className="text-right py-2 px-3 font-medium">Sharpe</th>
              </tr>
            </thead>
            <tbody>
              {selectedData.map((playbook, index) => (
                <tr key={playbook.playbook_name} className="border-b hover:bg-gray-50">
                  <td className="py-2 px-3 font-medium">{playbook.playbook_name}</td>
                  <td className="text-right py-2 px-3">{playbook.total_trades}</td>
                  <td className="text-right py-2 px-3">{playbook.win_rate.toFixed(1)}%</td>
                  <td className="text-right py-2 px-3">${playbook.avg_pnl.toFixed(2)}</td>
                  <td className={`text-right py-2 px-3 font-medium ${
                    playbook.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    ${playbook.total_pnl.toFixed(2)}
                  </td>
                  <td className="text-right py-2 px-3">{playbook.profit_factor.toFixed(2)}</td>
                  <td className="text-right py-2 px-3">{playbook.sharpe_ratio.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-2xl font-bold text-gray-900">Playbook Comparison</h2>

        <div className="flex flex-wrap gap-2">
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="1M">Last Month</option>
            <option value="3M">Last 3 Months</option>
            <option value="6M">Last 6 Months</option>
            <option value="1Y">Last Year</option>
            <option value="ALL">All Time</option>
          </select>

          <select
            value={comparisonType}
            onChange={(e) => setComparisonType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="win_rate">Win Rate</option>
            <option value="avg_pnl">Average P&L</option>
            <option value="profit_factor">Profit Factor</option>
            <option value="sharpe_ratio">Sharpe Ratio</option>
            <option value="consistency_score">Consistency</option>
          </select>
        </div>
      </div>

      {/* Playbook Selection */}
      <div className="bg-white p-4 rounded-lg shadow-sm border">
        <h3 className="text-sm font-medium mb-3">Select Playbooks to Compare:</h3>
        <div className="flex flex-wrap gap-2">
          {availablePlaybooks.map(playbook => (
            <button
              key={playbook}
              onClick={() => togglePlaybookSelection(playbook)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedPlaybooks.includes(playbook)
                  ? 'bg-blue-100 text-blue-800 border-2 border-blue-300'
                  : 'bg-gray-100 text-gray-700 border-2 border-transparent hover:bg-gray-200'
              }`}
            >
              {playbook}
            </button>
          ))}
        </div>
      </div>

      {selectedPlaybooks.length > 0 ? (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {renderComparisonChart()}
            {renderPerformanceTimeline()}
          </div>

          {renderSummaryTable()}

          {/* Key Insights */}
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">📊 Key Insights</h3>
            <div className="text-blue-800 space-y-1 text-sm">
              {comparisons.length > 0 && (
                <>
                  <p>• Best performing playbook: <strong>{comparisons.sort((a, b) => b.profit_factor - a.profit_factor)[0]?.playbook_name}</strong></p>
                  <p>• Highest win rate: <strong>{comparisons.sort((a, b) => b.win_rate - a.win_rate)[0]?.playbook_name}</strong> ({comparisons.sort((a, b) => b.win_rate - a.win_rate)[0]?.win_rate.toFixed(1)}%)</p>
                  <p>• Most consistent: <strong>{comparisons.sort((a, b) => b.consistency_score - a.consistency_score)[0]?.playbook_name}</strong></p>
                </>
              )}
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-500">Select playbooks above to compare their performance</p>
        </div>
      )}
    </div>
  );
};

export default PlaybookComparisonDashboard;