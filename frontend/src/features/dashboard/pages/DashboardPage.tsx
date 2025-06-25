
import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../../../store/auth';
import { useTradeStore } from '../../../store/trades';
import { MetricCard } from '../components/MetricCard';
import { EquityCurveChart } from '../components/EquityCurveChart';
import { Button } from '../../../components/ui/Button';

const DashboardPage: React.FC = () => {
  const { user, logout } = useAuthStore();
  const { 
    trades, 
    analytics, 
    isLoading, 
    error, 
    fetchTrades, 
    fetchAnalytics 
  } = useTradeStore();
  
  const [dateRange, setDateRange] = useState({
    start_date: '',
    end_date: ''
  });

  useEffect(() => {
    const loadData = async () => {
      await fetchTrades({ page: 1, per_page: 10 });
      await fetchAnalytics();
    };
    loadData();
  }, [fetchTrades, fetchAnalytics]);

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
  };

  const handleDateRangeChange = async () => {
    await fetchAnalytics(dateRange.start_date, dateRange.end_date);
  };

  if (isLoading && !trades.length) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">TradeSense Dashboard</h1>
              <p className="text-gray-600">Welcome back, {user?.username}!</p>
            </div>
            <Button onClick={handleLogout} variant="outline">
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Date Range Filter */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Analytics Period</h2>
          <div className="flex items-center space-x-4">
            <input
              type="date"
              value={dateRange.start_date}
              onChange={(e) => setDateRange(prev => ({ ...prev, start_date: e.target.value }))}
              className="border rounded px-3 py-2"
            />
            <span>to</span>
            <input
              type="date"
              value={dateRange.end_date}
              onChange={(e) => setDateRange(prev => ({ ...prev, end_date: e.target.value }))}
              className="border rounded px-3 py-2"
            />
            <Button onClick={handleDateRangeChange}>
              Update
            </Button>
          </div>
        </div>

        {/* Metrics Grid */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <MetricCard
              title="Total P&L"
              value={`$${analytics.total_pnl?.toFixed(2) || '0.00'}`}
              change={analytics.total_pnl >= 0 ? 'positive' : 'negative'}
            />
            <MetricCard
              title="Win Rate"
              value={`${(analytics.win_rate * 100)?.toFixed(1) || '0.0'}%`}
              change={analytics.win_rate >= 0.5 ? 'positive' : 'negative'}
            />
            <MetricCard
              title="Total Trades"
              value={analytics.total_trades?.toString() || '0'}
              change="neutral"
            />
            <MetricCard
              title="Profit Factor"
              value={analytics.profit_factor?.toFixed(2) || '0.00'}
              change={analytics.profit_factor >= 1 ? 'positive' : 'negative'}
            />
          </div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {analytics?.equity_curve && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Equity Curve</h3>
              <EquityCurveChart data={analytics.equity_curve} />
            </div>
          )}

          {analytics?.pnl_distribution && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">P&L Distribution</h3>
              <div className="space-y-2">
                {analytics.pnl_distribution.map((item, index) => (
                  <div key={index} className="flex justify-between">
                    <span>{item.range}</span>
                    <span className="font-medium">{item.count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Recent Trades */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold">Recent Trades</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Direction
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Entry Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    P&L
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {trades.slice(0, 10).map((trade) => (
                  <tr key={trade.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {trade.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className={`px-2 py-1 rounded text-xs ${
                        trade.direction === 'long' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {trade.direction.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ${trade.entry_price?.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {trade.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                        ${trade.pnl?.toFixed(2) || '0.00'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className={`px-2 py-1 rounded text-xs ${
                        trade.status === 'closed' 
                          ? 'bg-gray-100 text-gray-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {trade.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {trades.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No trades found. Start by adding your first trade!
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;
