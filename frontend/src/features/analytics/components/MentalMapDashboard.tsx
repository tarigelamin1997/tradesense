
import React, { useState, useEffect } from 'react';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { mentalMapService, MoodPattern, RuleBreakAnalysis, SessionReplay } from '../../../services/mentalMap';

export const MentalMapDashboard: React.FC = () => {
  const [moodPatterns, setMoodPatterns] = useState<MoodPattern | null>(null);
  const [ruleBreakAnalysis, setRuleBreakAnalysis] = useState<RuleBreakAnalysis | null>(null);
  const [recentSessions, setRecentSessions] = useState<SessionReplay[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDays, setSelectedDays] = useState(30);

  useEffect(() => {
    loadDashboardData();
  }, [selectedDays]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [mood, rules, sessions] = await Promise.all([
        mentalMapService.getMoodPatterns(selectedDays),
        mentalMapService.getRuleBreakAnalysis(selectedDays),
        mentalMapService.getSessions({ limit: 10 })
      ]);
      
      setMoodPatterns(mood);
      setRuleBreakAnalysis(rules);
      setRecentSessions(sessions);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getMoodColor = (mood: string) => {
    const colors = {
      calm: 'text-green-600',
      focused: 'text-blue-600',
      confident: 'text-purple-600',
      anxious: 'text-yellow-600',
      revenge: 'text-red-600',
      fearful: 'text-orange-600',
      frustrated: 'text-pink-600',
      euphoric: 'text-indigo-600',
      overconfident: 'text-red-700',
      uncertain: 'text-gray-600'
    };
    return colors[mood as keyof typeof colors] || 'text-gray-600';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Mental Map Dashboard</h1>
        <div className="flex items-center space-x-4">
          <select
            value={selectedDays}
            onChange={(e) => setSelectedDays(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Mood Patterns */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Mood Patterns</h2>
          
          {moodPatterns && Object.keys(moodPatterns.mood_distribution).length > 0 ? (
            <div className="space-y-4">
              {/* Mood Distribution */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Mood Distribution</h3>
                <div className="space-y-2">
                  {Object.entries(moodPatterns.mood_distribution)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 5)
                    .map(([mood, count]) => (
                      <div key={mood} className="flex items-center justify-between">
                        <span className={`text-sm font-medium ${getMoodColor(mood)}`}>
                          {mood}
                        </span>
                        <div className="flex items-center space-x-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{
                                width: `${(count / Math.max(...Object.values(moodPatterns.mood_distribution))) * 100}%`
                              }}
                            ></div>
                          </div>
                          <span className="text-sm text-gray-600">{count}</span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>

              {/* Insights */}
              {moodPatterns.insights.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Insights</h3>
                  <div className="space-y-1">
                    {moodPatterns.insights.map((insight, index) => (
                      <p key={index} className="text-sm text-gray-600">• {insight}</p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">No mood data available for this period</p>
          )}
        </Card>

        {/* Rule Break Analysis */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Rule Break Analysis</h2>
          
          {ruleBreakAnalysis && Object.keys(ruleBreakAnalysis.rule_break_distribution).length > 0 ? (
            <div className="space-y-4">
              {/* Rule Break Distribution */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Most Common Violations</h3>
                <div className="space-y-2">
                  {Object.entries(ruleBreakAnalysis.rule_break_distribution)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 5)
                    .map(([rule, count]) => (
                      <div key={rule} className="flex items-center justify-between">
                        <span className="text-sm text-gray-800">{rule}</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-red-600 h-2 rounded-full"
                              style={{
                                width: `${(count / Math.max(...Object.values(ruleBreakAnalysis.rule_break_distribution))) * 100}%`
                              }}
                            ></div>
                          </div>
                          <span className="text-sm text-gray-600">{count}</span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>

              {/* Insights */}
              {ruleBreakAnalysis.insights.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Insights</h3>
                  <div className="space-y-1">
                    {ruleBreakAnalysis.insights.map((insight, index) => (
                      <p key={index} className="text-sm text-gray-600">• {insight}</p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">No rule break data available for this period</p>
          )}
        </Card>
      </div>

      {/* Recent Sessions */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Recent Sessions</h2>
        
        {recentSessions.length > 0 ? (
          <div className="space-y-4">
            {recentSessions.map((session) => (
              <div key={session.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-grow">
                  <div className="flex items-center space-x-3">
                    <h3 className="font-medium text-gray-900">
                      {session.session_name || 'Untitled Session'}
                    </h3>
                    {session.dominant_mood && (
                      <span className={`text-sm font-medium ${getMoodColor(session.dominant_mood)}`}>
                        {session.dominant_mood}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                    <span>{formatDate(session.start_time)}</span>
                    <span>{session.total_trades} trades</span>
                    {session.rule_breaks && session.rule_breaks.length > 0 && (
                      <span className="text-red-600">
                        {session.rule_breaks.length} rule breaks
                      </span>
                    )}
                  </div>
                </div>
                <Button
                  onClick={() => window.location.href = `/mental-map/sessions/${session.id}`}
                  variant="outline"
                  size="sm"
                >
                  View Timeline
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">No sessions recorded yet</p>
            <Button
              onClick={() => window.location.href = '/mental-map/sessions/new'}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Start Your First Session
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};
