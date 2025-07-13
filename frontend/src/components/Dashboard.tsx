import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { analyticsService } from '../services/analytics';
import type { AnalyticsSummary } from '../services/analytics';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell 
} from 'recharts';
import { formatDateRange } from '../utils/date';
import { exportToCSV, formatDataForExport } from '../utils/export';

interface DashboardStats {
  totalPnl: number;
  winRate: number;
  totalTrades: number;
  avgHoldTime: string;
}

interface ChartData {
  equityCurve: Array<{ date: string; value: number }>;
  monthlyPnl: Array<{ month: string; pnl: number; trades: number }>;
  strategyBreakdown: Array<{ name: string; value: number; pnl: number }>;
}

const COLORS = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444'];

function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    totalPnl: 0,
    winRate: 0,
    totalTrades: 0,
    avgHoldTime: '0h'
  });
  const [chartData, setChartData] = useState<ChartData>({
    equityCurve: [],
    monthlyPnl: [],
    strategyBreakdown: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);
  const [dateRange, setDateRange] = useState(30); // Days
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchAnalytics = useCallback(async () => {
    try {
      if (!loading) setIsRefreshing(true);
      setError(null);
      
      // Get date range
      const { start, end } = formatDateRange(dateRange);
      
      // Check if user is authenticated
      const token = localStorage.getItem('authToken');
      if (!token) {
        throw new Error('Please log in to view analytics');
      }
      
      // Fetch analytics summary
      console.log('Fetching analytics with date range:', { start, end });
      console.log('Token in localStorage:', localStorage.getItem('authToken'));
      console.log('User in localStorage:', localStorage.getItem('currentUser'));
      
      const summary = await analyticsService.getSummary({
        start,
        end
      });
      console.log('Analytics summary received:', summary);
      
      // Update stats
      setStats({
        totalPnl: summary.total_pnl || 0,
        winRate: summary.overall_win_rate || 0,
        totalTrades: summary.total_trades || 0,
        avgHoldTime: '2.4h' // TODO: Calculate from actual data
      });

      // Process chart data
      processChartData(summary);

      // Simulate recent activity from strategy stats
      if (summary.strategy_stats && summary.strategy_stats.length > 0) {
        const activities = summary.strategy_stats.slice(0, 3).map((strategy, index) => ({
          id: index,
          type: strategy.total_pnl > 0 ? 'profit' : 'loss',
          description: `${strategy.name} Strategy`,
          amount: strategy.total_pnl,
          time: `${index + 1} hours ago`
        }));
        setRecentActivity(activities);
      }
    } catch (err: any) {
      console.error('Failed to fetch analytics:', err);
      console.error('Error details:', {
        message: err.message,
        response: err.response,
        status: err.response?.status,
        data: err.response?.data
      });
      
      // Check for specific error types
      if (err.message === 'Network Error' && !err.response) {
        // This usually means CORS issue or backend is down
        setError('Cannot connect to server. Please check if the backend is running.');
      } else if (err.response?.status === 401) {
        setError('Please log in to view analytics');
      } else if (err.response?.status === 404) {
        // No data found - show empty state
        setStats({
          totalPnl: 0,
          winRate: 0,
          totalTrades: 0,
          avgHoldTime: '0h'
        });
        setChartData({
          equityCurve: [],
          monthlyPnl: [],
          strategyBreakdown: []
        });
        setRecentActivity([]);
        setError(null); // Don't show error for empty data
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('Failed to load analytics data');
      }
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [loading, dateRange]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const processChartData = (summary: AnalyticsSummary) => {
    // Simulate equity curve data (in real app, this would come from API)
    const equityCurve = generateEquityCurve(summary.total_pnl, dateRange);
    
    // Monthly P&L data (simulated)
    const monthlyPnl = generateMonthlyPnl(summary.total_pnl, summary.total_trades);
    
    // Strategy breakdown
    const strategyBreakdown = summary.strategy_stats?.slice(0, 5).map(strategy => ({
      name: strategy.name,
      value: strategy.total_trades,
      pnl: strategy.total_pnl
    })) || [];

    setChartData({
      equityCurve,
      monthlyPnl,
      strategyBreakdown
    });
  };

  const generateEquityCurve = (totalPnl: number, days: number) => {
    const data = [];
    const endValue = totalPnl;
    const dailyChange = endValue / days;
    let cumulativeValue = 0;
    
    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      cumulativeValue += dailyChange + (Math.random() - 0.5) * (dailyChange * 2);
      data.push({
        date: date.toISOString().split('T')[0],
        value: Math.round(cumulativeValue * 100) / 100
      });
    }
    
    return data;
  };

  const generateMonthlyPnl = (totalPnl: number, totalTrades: number) => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    const avgPnlPerMonth = totalPnl / months.length;
    const avgTradesPerMonth = totalTrades / months.length;
    
    return months.map(month => ({
      month,
      pnl: Math.round((avgPnlPerMonth + (Math.random() - 0.5) * avgPnlPerMonth) * 100) / 100,
      trades: Math.floor(avgTradesPerMonth + (Math.random() - 0.5) * 10)
    }));
  };

  const formatCurrency = (value: number) => {
    const prefix = value >= 0 ? '+' : '';
    return `${prefix}$${Math.abs(value).toLocaleString()}`;
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const handleExport = useCallback(() => {
    const exportData = formatDataForExport(stats, chartData, dateRange);
    exportToCSV(exportData);
  }, [stats, chartData, dateRange]);

  const dateRangeDisplay = useMemo(() => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - dateRange);
    return `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`;
  }, [dateRange]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="text-sm font-medium">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.name.includes('$') || entry.dataKey === 'pnl' || entry.dataKey === 'value' 
                ? formatCurrency(entry.value) 
                : entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-red-600 mb-4">
            <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-gray-600">{error}</p>
          <button 
            onClick={fetchAnalytics}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative">
        {/* Refresh Overlay */}
        {isRefreshing && (
          <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="text-gray-600">Updating data...</span>
            </div>
          </div>
        )}
        {/* Header */}
        <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
            <p className="mt-2 text-gray-600">
              Track your trading performance and insights
              <span className="ml-2 text-sm text-gray-500">
                ({dateRangeDisplay})
              </span>
            </p>
          </div>
          <div className="mt-4 sm:mt-0 flex flex-col sm:flex-row gap-2">
            <select
              value={dateRange}
              onChange={(e) => setDateRange(Number(e.target.value))}
              className="block w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 3 months</option>
              <option value={180}>Last 6 months</option>
              <option value={365}>Last year</option>
            </select>
            <button
              onClick={handleExport}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Export CSV
            </button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className={`w-8 h-8 ${stats.totalPnl >= 0 ? 'bg-green-500' : 'bg-red-500'} rounded-full flex items-center justify-center`}>
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <h2 className="text-lg font-semibold text-gray-900">Total P&L</h2>
                <p className={`text-2xl font-bold ${stats.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(stats.totalPnl)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <h2 className="text-lg font-semibold text-gray-900">Win Rate</h2>
                <p className="text-2xl font-bold text-blue-600">{formatPercentage(stats.winRate)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <h2 className="text-lg font-semibold text-gray-900">Total Trades</h2>
                <p className="text-2xl font-bold text-purple-600">{stats.totalTrades}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <h2 className="text-lg font-semibold text-gray-900">Avg Hold Time</h2>
                <p className="text-2xl font-bold text-orange-600">{stats.avgHoldTime}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Equity Curve */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Equity Curve</h3>
            {chartData.equityCurve.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData.equityCurve}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  />
                  <YAxis tickFormatter={(value) => `$${value}`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    name="P&L"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-gray-500">
                No data available for the selected period
              </div>
            )}
          </div>

          {/* Monthly P&L */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly P&L</h3>
            {chartData.monthlyPnl.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData.monthlyPnl}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis tickFormatter={(value) => `$${value}`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar 
                    dataKey="pnl" 
                    fill="#10B981"
                    name="P&L"
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-gray-500">
                No data available for the selected period
              </div>
            )}
          </div>
        </div>

        {/* Bottom Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Strategy Breakdown */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Strategy Performance</h3>
            {chartData.strategyBreakdown.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={chartData.strategyBreakdown}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {chartData.strategyBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[250px] text-gray-500">
                No strategy data available
              </div>
            )}
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {recentActivity.length > 0 ? (
                  recentActivity.map((activity) => (
                    <div key={activity.id} className="flex items-center p-3 bg-gray-50 rounded-lg">
                      <div className={`flex-shrink-0 w-2 h-2 ${activity.type === 'profit' ? 'bg-green-500' : 'bg-red-500'} rounded-full`}></div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">{activity.description}</p>
                        <p className="text-sm text-gray-500">
                          {formatCurrency(activity.amount)} • {activity.time}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center py-4">No recent activity</p>
                )}
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4">
                <button className="flex flex-col items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors">
                  <svg className="w-8 h-8 text-blue-600 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <span className="text-sm font-medium text-blue-600">Upload</span>
                </button>

                <button 
                  onClick={handleExport}
                  className="flex flex-col items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
                >
                  <svg className="w-8 h-8 text-green-600 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  <span className="text-sm font-medium text-green-600">Export</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;