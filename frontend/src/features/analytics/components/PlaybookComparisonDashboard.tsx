import React, { useState, useEffect } from 'react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { playbookComparisonService } from '../../services/playbookComparison';
import Plot from 'react-plotly.js';

interface PlaybookMetrics {
  playbook_name: string;
  total_trades: number;
  win_rate: number;
  avg_pnl: number;
  profit_factor: number;
  max_drawdown: number;
  sharpe_ratio: number;
  total_pnl: number;
  avg_win: number;
  avg_loss: number;
  largest_win: number;
  largest_loss: number;
  consecutive_wins: number;
  consecutive_losses: number;
}

interface ComparisonData {
  playbooks: PlaybookMetrics[];
  period: string;
  equity_curves: { [key: string]: { dates: string[], values: number[] } };
  monthly_returns: { [key: string]: { months: string[], returns: number[] } };
}

interface PlaybookOption {
  id: string;
  name: string;
  description: string;
}

export const PlaybookComparisonDashboard: React.FC = () => {
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [availablePlaybooks, setAvailablePlaybooks] = useState<PlaybookOption[]>([]);
  const [selectedPlaybooks, setSelectedPlaybooks] = useState<string[]>([]);
  const [period, setPeriod] = useState('30d');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('metrics');

  useEffect(() => {
    loadAvailablePlaybooks();
  }, []);

  const loadAvailablePlaybooks = async () => {
    try {
      const playbooks = await playbookComparisonService.getAvailablePlaybooks();
      setAvailablePlaybooks(playbooks);
      if (playbooks.length >= 2) {
        setSelectedPlaybooks([playbooks[0].id, playbooks[1].id]);
      }
    } catch (error) {
      console.error('Failed to load playbooks:', error);
    }
  };

  const loadComparisonData = async () => {
    if (selectedPlaybooks.length < 2) return;

    setLoading(true);
    try {
      const data = await playbookComparisonService.comparePlaybooks(selectedPlaybooks, period);
      setComparisonData(data);
    } catch (error) {
      console.error('Failed to load comparison data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedPlaybooks.length >= 2) {
      loadComparisonData();
    }
  }, [selectedPlaybooks, period]);

  const handlePlaybookToggle = (playbookId: string) => {
    setSelectedPlaybooks(prev => {
      if (prev.includes(playbookId)) {
        return prev.filter(id => id !== playbookId);
      } else {
        return [...prev, playbookId];
      }
    });
  };

  const renderPlaybookSelector = () => (
    <Card className="p-4">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Select Playbooks to Compare</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {availablePlaybooks.map((playbook) => (
          <label key={playbook.id} className="flex items-center space-x-3 cursor-pointer">
            <input
              type="checkbox"
              checked={selectedPlaybooks.includes(playbook.id)}
              onChange={() => handlePlaybookToggle(playbook.id)}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <div>
              <span className="text-sm font-medium text-gray-900">{playbook.name}</span>
              <p className="text-xs text-gray-500">{playbook.description}</p>
            </div>
          </label>
        ))}
      </div>
    </Card>
  );

  const renderMetricsTable = () => {
    if (!comparisonData) return null;

    const getBestValue = (metric: keyof PlaybookMetrics, higher: boolean = true) => {
      const values = comparisonData.playbooks.map(p => p[metric] as number);
      return higher ? Math.max(...values) : Math.min(...values);
    };

    const isBest = (value: number, metric: keyof PlaybookMetrics, higher: boolean = true) => {
      return value === getBestValue(metric, higher);
    };

    return (
      <div className="overflow-x-auto">
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
                Total P&L
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Avg P&L
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Profit Factor
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Max DD
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Sharpe
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {comparisonData.playbooks.map((playbook) => (
              <tr key={playbook.playbook_name}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {playbook.playbook_name}
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                  isBest(playbook.total_trades, 'total_trades') ? 'font-bold text-green-600' : 'text-gray-500'
                }`}>
                  {playbook.total_trades}
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                  isBest(playbook.win_rate, 'win_rate') ? 'font-bold text-green-600' : 'text-gray-500'
                }`}>
                  {(playbook.win_rate * 100).toFixed(1)}%
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                  isBest(playbook.total_pnl, 'total_pnl') ? 'font-bold text-green-600' : 'text-gray-500'
                }`}>
                  ${playbook.total_pnl.toFixed(2)}
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                  isBest(playbook.avg_pnl, 'avg_pnl') ? 'font-bold text-green-600' : 'text-gray-500'
                }`}>
                  ${playbook.avg_pnl.toFixed(2)}
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                  isBest(playbook.profit_factor, 'profit_factor') ? 'font-bold text-green-600' : 'text-gray-500'
                }`}>
                  {playbook.profit_factor.toFixed(2)}
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                  isBest(playbook.max_drawdown, 'max_drawdown', false) ? 'font-bold text-green-600' : 'text-gray-500'
                }`}>
                  {(playbook.max_drawdown * 100).toFixed(1)}%
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                  isBest(playbook.sharpe_ratio, 'sharpe_ratio') ? 'font-bold text-green-600' : 'text-gray-500'
                }`}>
                  {playbook.sharpe_ratio.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderEquityCurveChart = () => {
    if (!comparisonData?.equity_curves) return null;

    const colors = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#F97316'];

    const traces = Object.entries(comparisonData.equity_curves).map(([playbook, data], index) => ({
      x: data.dates,
      y: data.values,
      type: 'scatter' as const,
      mode: 'lines' as const,
      name: playbook,
      line: { color: colors[index % colors.length], width: 2 }
    }));

    return (
      <Plot
        data={traces}
        layout={{
          title: 'Equity Curve Comparison',
          xaxis: { title: 'Date' },
          yaxis: { title: 'Cumulative P&L ($)' },
          hovermode: 'x unified',
          showlegend: true,
          height: 400,
          margin: { t: 40, r: 20, b: 40, l: 60 }
        }}
        style={{ width: '100%' }}
        config={{ responsive: true }}
      />
    );
  };

  const renderMonthlyReturnsChart = () => {
    if (!comparisonData?.monthly_returns) return null;

    const playbooks = Object.keys(comparisonData.monthly_returns);
    const months = comparisonData.monthly_returns[playbooks[0]]?.months || [];

    const traces = playbooks.map((playbook, index) => ({
      x: months,
      y: comparisonData.monthly_returns[playbook].returns,
      type: 'bar' as const,
      name: playbook,
      opacity: 0.8
    }));

    return (
      <Plot
        data={traces}
        layout={{
          title: 'Monthly Returns Comparison',
          xaxis: { title: 'Month' },
          yaxis: { title: 'Return (%)' },
          barmode: 'group',
          showlegend: true,
          height: 400,
          margin: { t: 40, r: 20, b: 40, l: 60 }
        }}
        style={{ width: '100%' }}
        config={{ responsive: true }}
      />
    );
  };

  const renderRadarChart = () => {
    if (!comparisonData) return null;

    const metrics = ['win_rate', 'profit_factor', 'sharpe_ratio'];
    const traces = comparisonData.playbooks.map((playbook, index) => ({
      type: 'scatterpolar' as const,
      r: [
        playbook.win_rate * 100,
        Math.min(playbook.profit_factor * 20, 100), // Scale to 0-100
        Math.max(Math.min((playbook.sharpe_ratio + 2) * 25, 100), 0) // Scale to 0-100
      ],
      theta: ['Win Rate (%)', 'Profit Factor', 'Sharpe Ratio'],
      fill: 'toself',
      name: playbook.playbook_name,
      opacity: 0.6
    }));

    return (
      <Plot
        data={traces}
        layout={{
          title: 'Performance Radar Chart',
          polar: {
            radialaxis: {
              visible: true,
              range: [0, 100]
            }
          },
          showlegend: true,
          height: 400
        }}
        style={{ width: '100%' }}
        config={{ responsive: true }}
      />
    );
  };

  const tabs = [
    { id: 'metrics', label: 'Metrics Table', icon: '📊' },
    { id: 'equity', label: 'Equity Curves', icon: '📈' },
    { id: 'monthly', label: 'Monthly Returns', icon: '📅' },
    { id: 'radar', label: 'Performance Radar', icon: '🎯' }
  ];

  return (
    <div className="space-y-6">
      {renderPlaybookSelector()}

      <Card className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">
            Playbook Comparison Dashboard
          </h2>

          <div className="flex gap-4">
            <select 
              value={period} 
              onChange={(e) => setPeriod(e.target.value)}
              className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="6m">Last 6 Months</option>
              <option value="1y">Last Year</option>
              <option value="all">All Time</option>
            </select>

            <Button onClick={loadComparisonData} disabled={loading || selectedPlaybooks.length < 2}>
              {loading ? 'Loading...' : 'Refresh Comparison'}
            </Button>
          </div>
        </div>

        {selectedPlaybooks.length < 2 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
            <p className="text-yellow-800">Please select at least 2 playbooks to compare.</p>
          </div>
        )}

        {comparisonData && selectedPlaybooks.length >= 2 && (
          <div className="space-y-6">
            {/* Tab Navigation */}
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                      activeTab === tab.id
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <span className="mr-2">{tab.icon}</span>
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            {/* Tab Content */}
            <div className="mt-6">
              {activeTab === 'metrics' && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Metrics</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Best values in each category are highlighted in green. Comparing {selectedPlaybooks.length} playbooks over {period}.
                  </p>
                  {renderMetricsTable()}
                </div>
              )}

              {activeTab === 'equity' && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Equity Curve Comparison</h3>
                  {renderEquityCurveChart()}
                </div>
              )}

              {activeTab === 'monthly' && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Monthly Returns</h3>
                  {renderMonthlyReturnsChart()}
                </div>
              )}

              {activeTab === 'radar' && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Radar</h3>
                  {renderRadarChart()}
                </div>
              )}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};