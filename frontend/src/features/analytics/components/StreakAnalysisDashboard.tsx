
import React, { useState, useEffect } from 'react';
import { Card } from '../../../components/ui/Card';
import { streaksService, StreakAnalysis } from '../../../services/streaks';

interface StreakAnalysisDashboardProps {
  className?: string;
}

export const StreakAnalysisDashboard: React.FC<StreakAnalysisDashboardProps> = ({
  className = ''
}) => {
  const [streakData, setStreakData] = useState<StreakAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStreakData();
  }, []);

  const fetchStreakData = async () => {
    try {
      setLoading(true);
      const data = await streaksService.getStreakAnalysis();
      setStreakData(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch streak data:', err);
      setError('Failed to load streak analysis');
    } finally {
      setLoading(false);
    }
  };

  const getConsistencyLabel = (score: number): { label: string; color: string } => {
    if (score >= 90) return { label: 'Rock-solid performer', color: 'text-green-600' };
    if (score >= 60) return { label: 'Generally consistent', color: 'text-blue-600' };
    if (score >= 30) return { label: 'Volatile performance', color: 'text-yellow-600' };
    return { label: 'Highly erratic', color: 'text-red-600' };
  };

  const getStreakStatus = (type: string, count: number): { icon: string; message: string; color: string } => {
    if (type === 'win') {
      return {
        icon: '🔥',
        message: `${count} Wins in a Row`,
        color: 'text-green-600 bg-green-50'
      };
    } else if (type === 'loss') {
      return {
        icon: '⛔️',
        message: `${count} Losses - Cool Off`,
        color: 'text-red-600 bg-red-50'
      };
    } else if (type === 'neutral') {
      return {
        icon: '➖',
        message: 'Neutral Session',
        color: 'text-gray-600 bg-gray-50'
      };
    }
    return {
      icon: '📊',
      message: 'No Active Streak',
      color: 'text-gray-600 bg-gray-50'
    };
  };

  if (loading) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !streakData) {
    return (
      <div className={`p-6 ${className}`}>
        <Card className="p-6 text-center">
          <div className="text-red-600 mb-2">⚠️ Error</div>
          <p className="text-gray-600">{error || 'No streak data available'}</p>
          <button
            onClick={fetchStreakData}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </Card>
      </div>
    );
  }

  const consistencyInfo = getConsistencyLabel(streakData.consistency_score);
  const currentStreakInfo = getStreakStatus(
    streakData.current_streak_type,
    streakData.current_streak
  );

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Streak & Consistency Analysis</h2>
        <button
          onClick={fetchStreakData}
          className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Current Streak Status */}
      <Card className={`p-6 ${currentStreakInfo.color} border-l-4`}>
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{currentStreakInfo.icon}</span>
          <div>
            <h3 className="font-semibold text-lg">{currentStreakInfo.message}</h3>
            <p className="text-sm opacity-75">
              {streakData.current_streak_details.recommendation}
            </p>
          </div>
        </div>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Max Win Streak */}
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <span className="text-green-600">🔼</span>
            <div>
              <p className="text-sm text-gray-600">Max Win Streak</p>
              <p className="text-2xl font-bold text-green-600">{streakData.max_win_streak}</p>
            </div>
          </div>
        </Card>

        {/* Max Loss Streak */}
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <span className="text-red-600">🔽</span>
            <div>
              <p className="text-sm text-gray-600">Max Loss Streak</p>
              <p className="text-2xl font-bold text-red-600">{streakData.max_loss_streak}</p>
            </div>
          </div>
        </Card>

        {/* Win Rate */}
        <Card className="p-4">
          <div className="text-center">
            <p className="text-sm text-gray-600">Session Win Rate</p>
            <p className="text-2xl font-bold text-blue-600">
              {streakData.total_sessions > 0 
                ? Math.round((streakData.win_sessions / streakData.total_sessions) * 100)
                : 0}%
            </p>
            <p className="text-xs text-gray-500">
              {streakData.win_sessions}W / {streakData.loss_sessions}L / {streakData.neutral_sessions}N
            </p>
          </div>
        </Card>

        {/* Consistency Score */}
        <Card className="p-4">
          <div className="text-center">
            <p className="text-sm text-gray-600">Consistency Score</p>
            <div className="relative pt-2">
              <div className="flex items-center justify-center">
                <div className="text-2xl font-bold">
                  {Math.round(streakData.consistency_score)}
                </div>
                <div className="text-sm text-gray-500 ml-1">/100</div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div
                  className="bg-gradient-to-r from-blue-500 to-green-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${streakData.consistency_score}%` }}
                ></div>
              </div>
              <p className={`text-xs mt-1 ${consistencyInfo.color}`}>
                {consistencyInfo.label}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Session Timeline */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Session Timeline</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {streakData.session_breakdown.slice(-10).map((session, index) => (
            <div
              key={session.date}
              className={`flex items-center justify-between p-3 rounded transition-colors ${
                session.outcome === 'win'
                  ? 'bg-green-50 border-l-4 border-green-400'
                  : session.outcome === 'loss'
                  ? 'bg-red-50 border-l-4 border-red-400'
                  : 'bg-gray-50 border-l-4 border-gray-400'
              }`}
            >
              <div className="flex items-center space-x-3">
                <span className="text-lg">
                  {session.outcome === 'win' ? '✅' : session.outcome === 'loss' ? '❌' : '➖'}
                </span>
                <div>
                  <p className="font-medium">{session.date}</p>
                  <p className="text-sm text-gray-600">{session.trade_count} trades</p>
                </div>
              </div>
              <div className="text-right">
                <p className={`font-semibold ${
                  session.pnl > 0 ? 'text-green-600' : session.pnl < 0 ? 'text-red-600' : 'text-gray-600'
                }`}>
                  ${session.pnl.toFixed(2)}
                </p>
                <p className="text-xs text-gray-500">
                  Avg: ${session.avg_trade_pnl.toFixed(2)}
                </p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Performance Insights */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Performance Insights</h3>
        <div className="space-y-3">
          {streakData.performance_insights.map((insight, index) => (
            <div
              key={index}
              className="flex items-start space-x-3 p-3 bg-blue-50 rounded border-l-4 border-blue-400"
            >
              <span className="text-blue-600 mt-0.5">💡</span>
              <p className="text-sm text-gray-700">{insight}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default StreakAnalysisDashboard;
