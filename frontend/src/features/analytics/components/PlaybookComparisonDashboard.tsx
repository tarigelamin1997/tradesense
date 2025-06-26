import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ResponsiveContainer, ScatterChart, Scatter, Cell
} from 'recharts';
import { playbookComparisonService, PlaybookComparisonData, CorrelationMatrixResponse, PerformanceOverTimeData } from '../../../services/playbookComparison';

interface PlaybookComparisonDashboardProps {
  selectedPlaybooks: string[];
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#ff00ff'];

export const PlaybookComparisonDashboard: React.FC<PlaybookComparisonDashboardProps> = ({ 
  selectedPlaybooks 
}) => {
  const [comparisonData, setComparisonData] = useState<PlaybookComparisonData[]>([]);
  const [correlationData, setCorrelationData] = useState<CorrelationMatrixResponse | null>(null);
  const [performanceOverTime, setPerformanceOverTime] = useState<PerformanceOverTimeData | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'trends' | 'correlation' | 'detailed'>('overview');
  const [timePeriod, setTimePeriod] = useState<'daily' | 'weekly' | 'monthly'>('daily');

  useEffect(() => {
    if (selectedPlaybooks.length >= 2) {
      loadAllData();
    }
  }, [selectedPlaybooks, timePeriod]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [comparison, correlation, performance] = await Promise.all([
        playbookComparisonService.comparePlaybooks(selectedPlaybooks),
        playbookComparisonService.getCorrelationMatrix(selectedPlaybooks),
        playbookComparisonService.getPerformanceOverTime(selectedPlaybooks, timePeriod)
      ]);

      setComparisonData(comparison.comparison_data);
      setCorrelationData(correlation);
      setPerformanceOverTime(performance);
    } catch (error) {
      console.error('Error loading comparison data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRankColor = (rank: number | undefined, total: number) => {
    if (!rank) return 'text-gray-500';
    if (rank === 1) return 'text-green-600 font-bold';
    if (rank === total) return 'text-red-600';
    return 'text-yellow-600';
  };

  const prepareRadarData = () => {
    if (!comparisonData.length) return [];

    const metrics = ['win_rate', 'profit_factor', 'expectancy', 'sharpe_ratio'];
    const maxValues = {
      win_rate: Math.max(...comparisonData.map(d => d.win_rate)),
      profit_factor: Math.max(...comparisonData.map(d => d.profit_factor)),
      expectancy: Math.max(...comparisonData.map(d => d.expectancy)),
      sharpe_ratio: Math.max(...comparisonData.map(d => d.sharpe_ratio))
    };

    return metrics.map(metric => {
      const dataPoint: any = { metric: metric.replace('_', ' ').toUpperCase() };
      comparisonData.forEach((playbook, index) => {
        const normalizedValue = (playbook[metric as keyof PlaybookComparisonData] as number) / maxValues[metric as keyof typeof maxValues] * 100;
        dataPoint[playbook.playbook_name] = Math.max(0, normalizedValue);
      });
      return dataPoint;
    });
  };

  const preparePerformanceTrendData = () => {
    if (!performanceOverTime?.performance_data) return [];

    const allPeriods = new Set<string>();
    Object.values(performanceOverTime.performance_data).forEach(data => {
      data.performance.forEach(p => allPeriods.add(p.period));
    });

    return Array.from(allPeriods).sort().map(period => {
      const dataPoint: any = { period };
      Object.entries(performanceOverTime.performance_data).forEach(([playbookId, data]) => {
        const periodData = data.performance.find(p => p.period === period);
        dataPoint[data.playbook_name] = periodData?.cumulative_pnl || 0;
      });
      return dataPoint;
    });
  };

  const prepareCorrelationData = () => {
    if (!correlationData?.correlation_matrix) return [];

    const matrix = correlationData.correlation_matrix;
    const data: Array<{x: string, y: string, value: number}> = [];

    Object.keys(matrix).forEach(id1 => {
      Object.keys(matrix[id1]).forEach(id2 => {
        if (id1 !== id2) {
          data.push({
            x: id1.substring(0, 8),
            y: id2.substring(0, 8),
            value: matrix[id1][id2]
          });
        }
      });
    });

    return data;
  };

  if (selectedPlaybooks.length < 2) {
    return (
      <div className="p-8 text-center bg-white rounded-lg shadow">
        <div className="text-6xl mb-4">📊</div>
        <h3 className="text-xl font-semibold mb-2">Compare Your Playbooks</h3>
        <p className="text-gray-600">Select at least 2 playbooks to start comparing their performance</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Analyzing playbook performance...</p>
      </div>
    );
  }

  const tabClasses = (tab: string) => 
    `px-4 py-2 rounded-lg font-medium transition-colors ${
      activeTab === tab 
        ? 'bg-blue-600 text-white' 
        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
    }`;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Playbook Comparison</h2>
        <div className="flex gap-2">
          <select 
            value={timePeriod} 
            onChange={(e) => setTimePeriod(e.target.value as any)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-2">
        <button onClick={() => setActiveTab('overview')} className={tabClasses('overview')}>
          Overview
        </button>
        <button onClick={() => setActiveTab('trends')} className={tabClasses('trends')}>
          Performance Trends
        </button>
        <button onClick={() => setActiveTab('correlation')} className={tabClasses('correlation')}>
          Correlation Analysis
        </button>
        <button onClick={() => setActiveTab('detailed')} className={tabClasses('detailed')}>
          Detailed Metrics
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metrics Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {comparisonData.map((playbook, index) => (
              <div key={playbook.playbook_id} className="bg-white p-6 rounded-lg shadow border-l-4" 
                   style={{borderLeftColor: COLORS[index % COLORS.length]}}>
                <h3 className="font-bold text-lg mb-4">{playbook.playbook_name}</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Win Rate:</span>
                    <span className={getRankColor(playbook.win_rate_rank, comparisonData.length)}>
                      {playbook.win_rate}% (#{playbook.win_rate_rank})
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Profit Factor:</span>
                    <span className={getRankColor(playbook.profit_factor_rank, comparisonData.length)}>
                      {playbook.profit_factor} (#{playbook.profit_factor_rank})
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total PnL:</span>
                    <span className={`${playbook.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'} font-semibold`}>
                      ${playbook.total_pnl}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Trades:</span>
                    <span>{playbook.total_trades}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Radar Chart for Performance Comparison */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">Performance Radar</h3>
            <ResponsiveContainer width="100%" height={400}>
              <RadarChart data={prepareRadarData()}>
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" />
                <PolarRadiusAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} />
                {comparisonData.map((playbook, index) => (
                  <Radar
                    key={playbook.playbook_id}
                    name={playbook.playbook_name}
                    dataKey={playbook.playbook_name}
                    stroke={COLORS[index % COLORS.length]}
                    fill={COLORS[index % COLORS.length]}
                    fillOpacity={0.2}
                  />
                ))}
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Performance Trends Tab */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">Cumulative Performance Over Time</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={preparePerformanceTrendData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" />
                <YAxis />
                <Tooltip formatter={(value: any) => [`$${value}`, 'Cumulative PnL']} />
                <Legend />
                {comparisonData.map((playbook, index) => (
                  <Line
                    key={playbook.playbook_id}
                    type="monotone"
                    dataKey={playbook.playbook_name}
                    stroke={COLORS[index % COLORS.length]}
                    strokeWidth={2}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Monthly Performance Bars */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">Monthly PnL Comparison</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="playbook_name" />
                <YAxis />
                <Tooltip formatter={(value: any) => [`$${value}`, 'Total PnL']} />
                <Bar dataKey="total_pnl">
                  {comparisonData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Correlation Tab */}
      {activeTab === 'correlation' && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-semibold mb-4">Performance Correlation Matrix</h3>
          {correlationData?.message ? (
            <p className="text-gray-600">{correlationData.message}</p>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <ScatterChart>
                <CartesianGrid />
                <XAxis type="category" dataKey="x" name="Playbook A" />
                <YAxis type="category" dataKey="y" name="Playbook B" />
                <Tooltip 
                  formatter={(value: any) => [`${value}`, 'Correlation']}
                  labelFormatter={(label) => `Correlation: ${label}`}
                />
                <Scatter name="Correlation" data={prepareCorrelationData()}>
                  {prepareCorrelationData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.value > 0.7 ? '#ff4444' : entry.value > 0.3 ? '#ffaa44' : '#44ff44'} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          )}
        </div>
      )}

      {/* Detailed Metrics Tab */}
      {activeTab === 'detailed' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b">
            <h3 className="text-xl font-semibold">Detailed Performance Metrics</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Playbook</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trades</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Win Rate</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Profit Factor</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expectancy</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sharpe Ratio</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Max DD</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Win</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Loss</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {comparisonData.map((playbook, index) => (
                  <tr key={playbook.playbook_id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-4 h-4 rounded mr-3" style={{backgroundColor: COLORS[index % COLORS.length]}}></div>
                        <div className="text-sm font-medium text-gray-900">{playbook.playbook_name}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{playbook.total_trades}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{playbook.win_rate}%</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{playbook.profit_factor}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${playbook.expectancy}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{playbook.sharpe_ratio}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">{playbook.max_drawdown}%</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">${playbook.avg_win}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">${playbook.avg_loss}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};