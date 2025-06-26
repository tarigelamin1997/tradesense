
import React, { useState, useEffect } from 'react';
import { Card } from '../../../components/ui/Card';
import { leaderboardService, GlobalLeaderboard, UserRanking } from '../../../services/leaderboard';

const GlobalLeaderboardComponent: React.FC = () => {
  const [leaderboard, setLeaderboard] = useState<GlobalLeaderboard | null>(null);
  const [userRanking, setUserRanking] = useState<UserRanking | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMetric, setSelectedMetric] = useState<'overall' | 'consistency' | 'win_rate' | 'profit_factor' | 'volume'>('overall');
  const [selectedTimeframe, setSelectedTimeframe] = useState<'all_time' | '30d' | '90d' | '1y'>('all_time');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [leaderboardData, rankingData] = await Promise.all([
          leaderboardService.getGlobalLeaderboard({
            metric: selectedMetric,
            timeframe: selectedTimeframe,
            limit: 50
          }),
          leaderboardService.getMyRanking()
        ]);
        
        setLeaderboard(leaderboardData);
        setUserRanking(rankingData);
      } catch (err) {
        setError('Failed to load leaderboard data');
        console.error('Error fetching leaderboard:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedMetric, selectedTimeframe]);

  const handleOptIn = async () => {
    try {
      await leaderboardService.optIntoLeaderboard();
      // Refresh user ranking
      const rankingData = await leaderboardService.getMyRanking();
      setUserRanking(rankingData);
    } catch (err) {
      console.error('Error opting into leaderboard:', err);
    }
  };

  const handleOptOut = async () => {
    try {
      await leaderboardService.optOutOfLeaderboard();
      // Refresh user ranking
      const rankingData = await leaderboardService.getMyRanking();
      setUserRanking(rankingData);
    } catch (err) {
      console.error('Error opting out of leaderboard:', err);
    }
  };

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

  return (
    <div className="space-y-6">
      {/* User Ranking Card */}
      {userRanking && (
        <Card className="p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold">Your Global Ranking</h2>
              <p className="text-gray-600">See how you stack up against other traders</p>
            </div>
            <div className="text-right">
              {userRanking.leaderboard_status.opted_in ? (
                <button
                  onClick={handleOptOut}
                  className="px-4 py-2 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                >
                  Opt Out
                </button>
              ) : (
                <button
                  onClick={handleOptIn}
                  className="px-4 py-2 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200"
                >
                  Join Leaderboard
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">#{userRanking.global_ranking.overall_rank}</div>
              <div className="text-sm text-gray-500">Overall Rank</div>
              <div className="text-xs text-gray-400">of {userRanking.global_ranking.total_users}</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">{userRanking.global_ranking.consistency_percentile.toFixed(0)}%</div>
              <div className="text-sm text-gray-500">Consistency</div>
              <div className="text-xs text-gray-400">Percentile</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">{userRanking.global_ranking.win_rate_percentile.toFixed(0)}%</div>
              <div className="text-sm text-gray-500">Win Rate</div>
              <div className="text-xs text-gray-400">Percentile</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600">{userRanking.global_ranking.profit_factor_percentile.toFixed(0)}%</div>
              <div className="text-sm text-gray-500">Profit Factor</div>
              <div className="text-xs text-gray-400">Percentile</div>
            </div>
          </div>

          {userRanking.improvement_suggestions.length > 0 && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-2">Improvement Suggestions</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                {userRanking.improvement_suggestions.map((suggestion, index) => (
                  <li key={index}>• {suggestion}</li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}

      {/* Leaderboard Controls */}
      <div className="flex flex-wrap gap-4 items-center">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Metric</label>
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value as any)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value="overall">Overall</option>
            <option value="consistency">Consistency</option>
            <option value="win_rate">Win Rate</option>
            <option value="profit_factor">Profit Factor</option>
            <option value="volume">Volume</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Timeframe</label>
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value as any)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value="all_time">All Time</option>
            <option value="1y">1 Year</option>
            <option value="90d">90 Days</option>
            <option value="30d">30 Days</option>
          </select>
        </div>
      </div>

      {/* Global Leaderboard */}
      {leaderboard && (
        <Card className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-semibold">Global Leaderboard</h3>
            <div className="text-sm text-gray-500">
              {leaderboard.total_participants} participants
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-2">Rank</th>
                  <th className="text-left py-3 px-2">Trader</th>
                  <th className="text-right py-3 px-2">Consistency</th>
                  <th className="text-right py-3 px-2">Win Rate</th>
                  <th className="text-right py-3 px-2">Profit Factor</th>
                  <th className="text-right py-3 px-2">Trades</th>
                  <th className="text-right py-3 px-2">Accounts</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.rankings.map((entry) => (
                  <tr key={entry.rank} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-2">
                      <div className="flex items-center">
                        {entry.rank <= 3 && (
                          <span className="mr-2">
                            {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : '🥉'}
                          </span>
                        )}
                        #{entry.rank}
                      </div>
                    </td>
                    <td className="py-3 px-2">
                      <div>
                        <div className="font-medium">{entry.display_name}</div>
                        <div className="text-xs text-gray-500">Joined {entry.joined_date}</div>
                      </div>
                    </td>
                    <td className="py-3 px-2 text-right font-semibold text-green-600">
                      {entry.consistency_score.toFixed(1)}%
                    </td>
                    <td className="py-3 px-2 text-right">
                      {entry.win_rate.toFixed(1)}%
                    </td>
                    <td className="py-3 px-2 text-right">
                      {entry.profit_factor.toFixed(2)}
                    </td>
                    <td className="py-3 px-2 text-right">
                      {entry.total_trades}
                    </td>
                    <td className="py-3 px-2 text-right">
                      {entry.account_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};

export default GlobalLeaderboardComponent;
