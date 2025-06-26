
import React, { useState, useEffect } from 'react';
import { Line, Bar, Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { playbookService } from '../../../services/playbooks';
import { analyticsService } from '../../../services/analytics';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface PlaybookMetrics {
  id: string;
  name: string;
  totalTrades: number;
  winRate: number;
  profitFactor: number;
  expectancy: number;
  maxDrawdown: number;
  sharpeRatio: number;
  avgWin: number;
  avgLoss: number;
  totalPnL: number;
  monthlyReturns: number[];
  equityCurve: { date: string; value: number }[];
}

const PlaybookComparisonDashboard: React.FC = () => {
  const [playbooks, setPlaybooks] = useState<string[]>([]);
  const [selectedPlaybooks, setSelectedPlaybooks] = useState<string[]>([]);
  const [comparisonData, setComparisonData] = useState<PlaybookMetrics[]>([]);
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('6M');
  const [comparisonType, setComparisonType] = useState<'performance' | 'risk' | 'consistency'>('performance');

  useEffect(() => {
    loadPlaybooks();
  }, []);

  useEffect(() => {
    if (selectedPlaybooks.length > 0) {
      loadComparisonData();
    }
  }, [selectedPlaybooks, timeRange]);

  const loadPlaybooks = async () => {
    try {
      const response = await playbookService.getPlaybooks();
      setPlaybooks(response.data.map((p: any) => p.name));
    } catch (error) {
      console.error('Failed to load playbooks:', error);
    }
  };

  const loadComparisonData = async () => {
    setLoading(true);
    try {
      const promises = selectedPlaybooks.map(async (playbookName) => {
        const metrics = await analyticsService.getPlaybookMetrics(playbookName, timeRange);
        return {
          id: playbookName,
          name: playbookName,
          ...metrics
        };
      });
      
      const results = await Promise.all(promises);
      setComparisonData(results);
    } catch (error) {
      console.error('Failed to load comparison data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePlaybookToggle = (playbook: string) => {
    setSelectedPlaybooks(prev => 
      prev.includes(playbook) 
        ? prev.filter(p => p !== playbook)
        : [...prev, playbook].slice(0, 5) // Limit to 5 playbooks
    );
  };

  const generateColors = (count: number) => {
    const colors = [
      'rgba(75, 192, 192, 0.8)',
      'rgba(255, 99, 132, 0.8)',
      'rgba(54, 162, 235, 0.8)',
      'rgba(255, 206, 86, 0.8)',
      'rgba(153, 102, 255, 0.8)'
    ];
    return colors.slice(0, count);
  };

  const getPerformanceChartData = () => {
    if (comparisonData.length === 0) return null;

    return {
      labels: ['Win Rate %', 'Profit Factor', 'Expectancy', 'Sharpe Ratio', 'Total PnL'],
      datasets: comparisonData.map((playbook, index) => ({
        label: playbook.name,
        data: [
          playbook.winRate,
          playbook.profitFactor,
          playbook.expectancy,
          playbook.sharpeRatio,
          playbook.totalPnL / 1000 // Scale down for radar chart
        ],
        backgroundColor: generateColors(comparisonData.length)[index],
        borderColor: generateColors(comparisonData.length)[index],
        borderWidth: 2,
        fill: false
      }))
    };
  };

  const getEquityCurveData = () => {
    if (comparisonData.length === 0) return null;

    // Get all unique dates and sort them
    const allDates = [...new Set(
      comparisonData.flatMap(p => p.equityCurve.map(point => point.date))
    )].sort();

    return {
      labels: allDates,
      datasets: comparisonData.map((playbook, index) => ({
        label: playbook.name,
        data: allDates.map(date => {
          const point = playbook.equityCurve.find(p => p.date === date);
          return point ? point.value : null;
        }),
        borderColor: generateColors(comparisonData.length)[index],
        backgroundColor: generateColors(comparisonData.length)[index],
        fill: false,
        spanGaps: true
      }))
    };
  };

  const getMetricsComparisonData = () => {
    if (comparisonData.length === 0) return null;

    const metrics = ['Win Rate', 'Profit Factor', 'Max Drawdown', 'Total Trades'];
    
    return {
      labels: comparisonData.map(p => p.name),
      datasets: metrics.map((metric, index) => ({
        label: metric,
        data: comparisonData.map(p => {
          switch (metric) {
            case 'Win Rate': return p.winRate;
            case 'Profit Factor': return p.profitFactor;
            case 'Max Drawdown': return Math.abs(p.maxDrawdown);
            case 'Total Trades': return p.totalTrades;
            default: return 0;
          }
        }),
        backgroundColor: generateColors(metrics.length)[index]
      }))
    };
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Playbook Performance Comparison',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  const radarOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Multi-Dimensional Performance Radar',
      },
    },
    scales: {
      r: {
        beginAtZero: true,
      },
    },
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          Multi-Playbook Comparison Dashboard
        </h2>
        
        {/* Controls */}
        <div className="flex flex-wrap gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Time Range
            </label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="1M">1 Month</option>
              <option value="3M">3 Months</option>
              <option value="6M">6 Months</option>
              <option value="1Y">1 Year</option>
              <option value="ALL">All Time</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Comparison Type
            </label>
            <select
              value={comparisonType}
              onChange={(e) => setComparisonType(e.target.value as any)}
              className="border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="performance">Performance</option>
              <option value="risk">Risk Analysis</option>
              <option value="consistency">Consistency</option>
            </select>
          </div>
        </div>

        {/* Playbook Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Playbooks to Compare (Max 5)
          </label>
          <div className="flex flex-wrap gap-2">
            {playbooks.map(playbook => (
              <button
                key={playbook}
                onClick={() => handlePlaybookToggle(playbook)}
                className={`px-4 py-2 rounded-md border ${
                  selectedPlaybooks.includes(playbook)
                    ? 'bg-blue-500 text-white border-blue-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {playbook}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="mt-2 text-gray-600">Loading comparison data...</p>
        </div>
      )}

      {!loading && selectedPlaybooks.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          Select playbooks above to start comparing performance metrics
        </div>
      )}

      {!loading && comparisonData.length > 0 && (
        <div className="space-y-8">
          {/* Performance Summary Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white border border-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Playbook
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Trades
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Win Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Profit Factor
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total P&L
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Max Drawdown
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sharpe Ratio
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {comparisonData.map((playbook) => (
                  <tr key={playbook.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {playbook.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {playbook.totalTrades}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {playbook.winRate.toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {playbook.profitFactor.toFixed(2)}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm ${playbook.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${playbook.totalPnL.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                      {playbook.maxDrawdown.toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {playbook.sharpeRatio.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Equity Curves Comparison */}
            {getEquityCurveData() && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4">Equity Curve Comparison</h3>
                <Line data={getEquityCurveData()!} options={chartOptions} />
              </div>
            )}

            {/* Performance Radar Chart */}
            {getPerformanceChartData() && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4">Performance Radar</h3>
                <Radar data={getPerformanceChartData()!} options={radarOptions} />
              </div>
            )}

            {/* Metrics Bar Chart */}
            {getMetricsComparisonData() && (
              <div className="bg-gray-50 p-4 rounded-lg lg:col-span-2">
                <h3 className="text-lg font-semibold mb-4">Key Metrics Comparison</h3>
                <Bar data={getMetricsComparisonData()!} options={chartOptions} />
              </div>
            )}
          </div>

          {/* Ranking Section */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg">
            <h3 className="text-lg font-semibold mb-4">Playbook Rankings</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Best Win Rate</h4>
                {[...comparisonData].sort((a, b) => b.winRate - a.winRate).slice(0, 3).map((playbook, index) => (
                  <div key={playbook.id} className="flex justify-between items-center py-1">
                    <span className="text-sm">{index + 1}. {playbook.name}</span>
                    <span className="text-sm font-medium text-green-600">{playbook.winRate.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
              
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Best Profit Factor</h4>
                {[...comparisonData].sort((a, b) => b.profitFactor - a.profitFactor).slice(0, 3).map((playbook, index) => (
                  <div key={playbook.id} className="flex justify-between items-center py-1">
                    <span className="text-sm">{index + 1}. {playbook.name}</span>
                    <span className="text-sm font-medium text-blue-600">{playbook.profitFactor.toFixed(2)}</span>
                  </div>
                ))}
              </div>
              
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Best Total P&L</h4>
                {[...comparisonData].sort((a, b) => b.totalPnL - a.totalPnL).slice(0, 3).map((playbook, index) => (
                  <div key={playbook.id} className="flex justify-between items-center py-1">
                    <span className="text-sm">{index + 1}. {playbook.name}</span>
                    <span className={`text-sm font-medium ${playbook.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${playbook.totalPnL.toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PlaybookComparisonDashboard;
