
import React, { useEffect } from 'react';
import { 
  CurrencyDollarIcon, 
  TrendingUpIcon, 
  ChartBarIcon, 
  DocumentTextIcon 
} from '@heroicons/react/24/outline';
import { useAuthStore } from '../../../store/auth';
import { useTradeStore } from '../../../store/trades';
import { MetricCard, EquityCurveChart, WinRateGauge } from '../components';

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const { analytics, fetchAnalytics, isLoading } = useTradeStore();

  useEffect(() => {
    if (user) {
      fetchAnalytics();
    }
  }, [user, fetchAnalytics]);

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-8"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Trading Analytics Dashboard</h1>
        <p className="mt-2 text-gray-600">Advanced insights for data-driven trading decisions</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total P&L"
          value={analytics?.total_pnl || 0}
          change={12.5}
          icon={CurrencyDollarIcon}
          trend={analytics?.total_pnl && analytics.total_pnl > 0 ? 'up' : 'down'}
          format="currency"
        />
        <MetricCard
          title="Win Rate"
          value={analytics?.win_rate || 0}
          change={2.1}
          icon={TrendingUpIcon}
          trend="up"
          format="percentage"
        />
        <MetricCard
          title="Profit Factor"
          value={analytics?.profit_factor || 0}
          change={0.15}
          icon={ChartBarIcon}
          trend={analytics?.profit_factor && analytics.profit_factor > 1.5 ? 'up' : 'down'}
        />
        <MetricCard
          title="Total Trades"
          value={analytics?.total_trades || 0}
          icon={DocumentTextIcon}
          trend="neutral"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <EquityCurveChart data={analytics?.equity_curve || []} />
        <WinRateGauge winRate={analytics?.win_rate || 0} />
      </div>
    </div>
  );
};
