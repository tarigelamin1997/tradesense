
import React, { useState, useEffect } from 'react';
import { Card } from '../../../components/ui/Card';
import { leaderboardService, CrossAccountAnalytics } from '../../../services/leaderboard';

interface AccountPerformanceCardProps {
  account: any;
}

const AccountPerformanceCard: React.FC<AccountPerformanceCardProps> = ({ account }) => {
  const getAccountTypeColor = (type: string) => {
    switch (type) {
      case 'funded': return 'bg-green-100 text-green-800';
      case 'live': return 'bg-blue-100 text-blue-800';
      case 'sim': return 'bg-gray-100 text-gray-800';
      case 'demo': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card className="p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold">{account.account_name}</h3>
          <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getAccountTypeColor(account.account_type)}`}>
            {account.account_type?.toUpperCase() || 'UNKNOWN'}
          </span>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold">{account.performance_grade}</div>
          <div className="text-sm text-gray-500">Grade</div>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-sm text-gray-500">Win Rate</div>
          <div className="text-lg font-semibold">{account.stats.win_rate.toFixed(1)}%</div>
        </div>
        <div>
          <div className="text-sm text-gray-500">Profit Factor</div>
          <div className="text-lg font-semibold">{account.stats.profit_factor.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-sm text-gray-500">Trades</div>
          <div className="text-lg font-semibold">{account.stats.trade_count}</div>
        </div>
        <div>
          <div className="text-sm text-gray-500">Consistency</div>
          <div className="text-lg font-semibold">{account.stats.consistency_score.toFixed(1)}%</div>
        </div>
      </div>
      
      <div className="mt-4">
        <div className="text-sm text-gray-500">Total P&L</div>
        <div className={`text-xl font-bold ${account.stats.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          ${account.stats.total_pnl.toFixed(2)}
        </div>
      </div>
    </Card>
  );
};

const CrossAccountDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<CrossAccountAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const data = await leaderboardService.getCrossAccountAnalytics();
        setAnalytics(data);
      } catch (err) {
        setError('Failed to load cross-account analytics');
        console.error('Error fetching cross-account analytics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-600 p-8">
        <p>{error}</p>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center text-gray-500 p-8">
        <p>No analytics data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Aggregate Performance Summary */}
      <Card className="p-6">
        <h2 className="text-2xl font-bold mb-6">Cross-Account Performance Summary</h2>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{analytics.aggregate_performance.total_accounts}</div>
            <div className="text-sm text-gray-500">Active Accounts</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold">{analytics.aggregate_performance.total_trades}</div>
            <div className="text-sm text-gray-500">Total Trades</div>
          </div>
          <div className="text-center">
            <div className={`text-3xl font-bold ${analytics.aggregate_performance.overall_win_rate >= 50 ? 'text-green-600' : 'text-red-600'}`}>
              {analytics.aggregate_performance.overall_win_rate.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500">Overall Win Rate</div>
          </div>
          <div className="text-center">
            <div className={`text-3xl font-bold ${analytics.aggregate_performance.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${analytics.aggregate_performance.total_pnl.toFixed(0)}
            </div>
            <div className="text-sm text-gray-500">Total P&L</div>
          </div>
        </div>
      </Card>

      {/* Account Comparison */}
      <div>
        <h3 className="text-xl font-semibold mb-4">Account Performance Comparison</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {analytics.account_comparison.map((account) => (
            <AccountPerformanceCard key={account.account_id} account={account} />
          ))}
        </div>
      </div>

      {/* Insights */}
      {analytics.insights.length > 0 && (
        <Card className="p-6">
          <h3 className="text-xl font-semibold mb-4">Key Insights</h3>
          <ul className="space-y-2">
            {analytics.insights.map((insight, index) => (
              <li key={index} className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span>{insight}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Recommendations */}
      {analytics.recommendations.length > 0 && (
        <Card className="p-6">
          <h3 className="text-xl font-semibold mb-4">Recommendations</h3>
          <ul className="space-y-2">
            {analytics.recommendations.map((recommendation, index) => (
              <li key={index} className="flex items-start">
                <span className="text-green-500 mr-2">→</span>
                <span>{recommendation}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
};

export default CrossAccountDashboard;
