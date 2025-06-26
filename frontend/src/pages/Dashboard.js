import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../stores/authStore';
import { useDataStore } from '../stores/dataStore';
import { api } from '../lib/api';
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  DocumentTextIcon,
  CloudArrowUpIcon
} from '@heroicons/react/24/outline';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { Link } from 'react-router-dom';
import { analyticsService } from '../services/analytics';

const Dashboard = () => {
  const { user } = useAuthStore();
  const { 
    tradeData, 
    analytics, 
    isLoading, 
    uploadData, 
    analyzeData, 
    setAnalytics 
  } = useDataStore();

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [activeTab, setActiveTab] = useState('overview');
  const [quickStats, setQuickStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      fetchDashboardData();
      loadQuickStats();
    }
  }, [user]);

  const fetchDashboardData = async () => {
    try {
      const response = await api.get(`/analytics/dashboard/${user.user_id}`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    }
  };

  const loadQuickStats = async () => {
    try {
      const data = await analyticsService.getSummary();
      setQuickStats(data);
    } catch (error) {
      console.error('Failed to load quick stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setSelectedFile(file);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await uploadData(formData, (progress) => {
        setUploadProgress(progress);
      });

      if (response.success) {
        // Automatically analyze uploaded data
        await analyzeData(response.data);
        await fetchDashboardData();
      }
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const MetricCard = ({ title, value, change, icon: Icon, trend }) => (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${trend === 'up' ? 'bg-green-100' : trend === 'down' ? 'bg-red-100' : 'bg-blue-100'}`}>
            <Icon className={`h-6 w-6 ${trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-blue-600'}`} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
          </div>
        </div>
        {change && (
          <div className={`flex items-center space-x-1 ${change.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
            {change.startsWith('+') ? (
              <TrendingUpIcon className="h-4 w-4" />
            ) : (
              <TrendingDownIcon className="h-4 w-4" />
            )}
            <span className="text-sm font-medium">{change}</span>
          </div>
        )}
      </div>
    </div>
  );

  const EquityCurveChart = ({ data }) => (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip 
          formatter={(value) => [`$${value.toLocaleString()}`, 'Cumulative P&L']}
          labelFormatter={(label) => `Trade: ${label}`}
        />
        <Area 
          type="monotone" 
          dataKey="cumulativePnL" 
          stroke="#3B82F6" 
          fill="#3B82F6" 
          fillOpacity={0.2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );

  const PnLDistribution = ({ data }) => (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="range" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="count" fill="#10B981" />
      </BarChart>
    </ResponsiveContainer>
  );

  const WinRateGauge = ({ winRate }) => {
    const data = [
      { name: 'Win Rate', value: winRate, fill: '#10B981' },
      { name: 'Loss Rate', value: 100 - winRate, fill: '#EF4444' }
    ];

    return (
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  if (!tradeData && !analytics) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <CloudArrowUpIcon className="mx-auto h-24 w-24 text-gray-400" />
            <h2 className="mt-4 text-3xl font-bold text-gray-900">Welcome to TradeSense</h2>
            <p className="mt-2 text-lg text-gray-600">Upload your trade data to begin advanced analytics</p>

            <div className="mt-8 max-w-md mx-auto">
              <label className="flex justify-center w-full h-32 px-4 transition bg-white border-2 border-gray-300 border-dashed rounded-md appearance-none cursor-pointer hover:border-gray-400 focus:outline-none">
                <span className="flex items-center space-x-2">
                  <DocumentTextIcon className="w-6 h-6 text-gray-600" />
                  <span className="font-medium text-gray-600">
                    Drop files to upload, or <span className="text-blue-600 underline">browse</span>
                  </span>
                </span>
                <input 
                  type="file" 
                  name="file_upload" 
                  className="hidden" 
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileUpload}
                />
              </label>
              {uploadProgress > 0 && (
                <div className="mt-4">
                  <div className="bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                  <p className="text-sm text-gray-600 mt-2">{uploadProgress}% uploaded</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Trading Analytics Dashboard</h1>
          <p className="mt-2 text-gray-600">Advanced insights for data-driven trading decisions</p>
        </div>

        {/* Quick Analytics Preview */}
        {!loading && quickStats && (
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Quick Insights</h2>
              <Link 
                to="/analytics" 
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm font-medium"
              >
                View Full Analytics →
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="text-sm font-medium text-gray-500">Total Trades</h3>
                <p className="text-2xl font-bold text-gray-900">{quickStats.total_trades}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="text-sm font-medium text-gray-500">Win Rate</h3>
                <p className="text-2xl font-bold text-gray-900">{quickStats.overall_win_rate?.toFixed(1)}%</p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="text-sm font-medium text-gray-500">Total P&L</h3>
                <p className={`text-2xl font-bold ${quickStats.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ${quickStats.total_pnl?.toFixed(2)}
                </p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="text-sm font-medium text-gray-500">Emotional Cost</h3>
                <p className="text-2xl font-bold text-red-600">
                  ${(quickStats.hesitation_cost + Math.abs(quickStats.fomo_impact) + quickStats.revenge_trading_cost)?.toFixed(0)}
                </p>
              </div>
            </div>

            {/* Key Insights */}
            {quickStats.emotional_leaks?.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
                <h3 className="text-lg font-medium text-red-800 mb-2">🚨 Emotional Leak Alert</h3>
                <p className="text-red-700">
                  Your biggest leak: <strong>{quickStats.emotional_leaks[0]?.name}</strong> 
                  has cost you <strong>${quickStats.emotional_leaks[0]?.cost?.toFixed(0)}</strong> 
                  across {quickStats.emotional_leaks[0]?.frequency} trades.
                </p>
                <p className="text-sm text-red-600 mt-1">{quickStats.emotional_leaks[0]?.description}</p>
              </div>
            )}

            {quickStats.most_profitable_emotion && (
              <div className="bg-green-50 border border-green-200 rounded-md p-4">
                <h3 className="text-lg font-medium text-green-800 mb-2">✅ Your Best Trading State</h3>
                <p className="text-green-700">
                  You perform best when feeling <strong>"{quickStats.most_profitable_emotion}"</strong>. 
                  Try to cultivate this mindset before trading.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Total P&L"
            value={`$${analytics?.total_pnl?.toLocaleString() || '0'}`}
            change={analytics?.total_pnl > 0 ? '+12.5%' : '-5.2%'}
            icon={CurrencyDollarIcon}
            trend={analytics?.total_pnl > 0 ? 'up' : 'down'}
          />
          <MetricCard
            title="Win Rate"
            value={`${analytics?.win_rate?.toFixed(1) || '0'}%`}
            change="+2.1%"
            icon={TrendingUpIcon}
            trend="up"
          />
          <MetricCard
            title="Profit Factor"
            value={analytics?.profit_factor?.toFixed(2) || '0'}
            change={analytics?.profit_factor > 1.5 ? '+0.15' : '-0.08'}
            icon={ChartBarIcon}
            trend={analytics?.profit_factor > 1.5 ? 'up' : 'down'}
          />
          <MetricCard
            title="Total Trades"
            value={analytics?.total_trades?.toLocaleString() || '0'}
            change="+47"
            icon={DocumentTextIcon}
            trend="up"
          />
        </div>

        {/* Navigation Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'overview', name: 'Overview' },
              { id: 'performance', name: 'Performance' },
              { id: 'analysis', name: 'Analysis' },
              { id: 'risk', name: 'Risk Management' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Equity Curve</h3>
              <EquityCurveChart data={analytics?.equity_curve || []} />
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Win Rate Distribution</h3>
              <WinRateGauge winRate={analytics?.win_rate || 0} />
              <div className="text-center mt-4">
                <p className="text-2xl font-bold text-gray-900">{analytics?.win_rate?.toFixed(1) || '0'}%</p>
                <p className="text-sm text-gray-600">Overall Win Rate</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'performance' && (
          <div className="grid grid-cols-1 gap-8">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">P&L Distribution</h3>
              <PnLDistribution data={analytics?.pnl_distribution || []} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 text-center">
                <h4 className="text-sm font-medium text-gray-600">Best Day</h4>
                <p className="text-2xl font-bold text-green-600">${analytics?.best_day?.toLocaleString() || '0'}</p>
              </div>
              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 text-center">
                <h4 className="text-sm font-medium text-gray-600">Worst Day</h4>
                <p className="text-2xl font-bold text-red-600">${analytics?.worst_day?.toLocaleString() || '0'}</p>
              </div>
              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 text-center">
                <h4 className="text-sm font-medium text-gray-600">Avg Daily P&L</h4>
                <p className="text-2xl font-bold text-gray-900">${analytics?.avg_daily_pnl?.toLocaleString() || '0'}</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Trade Analysis</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trades</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Win Rate</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {(analytics?.symbol_breakdown || []).map((symbol, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{symbol.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{symbol.trades}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{symbol.winRate}%</td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm ${symbol.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${symbol.pnl.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'risk' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Metrics</h3>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-600">Max Drawdown</span>
                  <span className="font-semibold text-red-600">${analytics?.max_drawdown?.toLocaleString() || '0'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Sharpe Ratio</span>
                  <span className="font-semibold">{analytics?.sharpe_ratio?.toFixed(2) || '0'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Risk/Reward Ratio</span>
                  <span className="font-semibold">{analytics?.risk_reward_ratio?.toFixed(2) || '0'}</span>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Position Sizing Recommendations</h3>
              <div className="space-y-3">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-800">Recommended position size: 2.5% of account per trade</p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="text-sm text-green-800">Current risk level: Conservative</p>
                </div>
                <div className="p-4 bg-yellow-50 rounded-lg">
                  <p className="text-sm text-yellow-800">Consider tightening stop losses on trending positions</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;