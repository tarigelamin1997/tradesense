
import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import emotionsService, { EmotionPerformanceStats, PlanExecutionAnalysis, EmotionalTrends } from '../../../services/emotions';

const EmotionalAnalyticsDashboard: React.FC = () => {
  const [emotionStats, setEmotionStats] = useState<EmotionPerformanceStats>({});
  const [planAnalysis, setPlanAnalysis] = useState<PlanExecutionAnalysis | null>(null);
  const [trends, setTrends] = useState<EmotionalTrends | null>(null);
  const [insights, setInsights] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        const [emotionData, planData, trendsData, insightsData] = await Promise.all([
          emotionsService.getPerformanceCorrelation(),
          emotionsService.getPlanExecutionAnalysis(),
          emotionsService.getEmotionalTrends(30),
          emotionsService.getEmotionalInsights()
        ]);

        setEmotionStats(emotionData);
        setPlanAnalysis(planData);
        setTrends(trendsData);
        setInsights(insightsData);
      } catch (error) {
        console.error('Failed to load emotional analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    loadAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">Loading emotional analytics...</div>
      </div>
    );
  }

  const emotionChartData = Object.entries(emotionStats).map(([emotion, stats]) => ({
    emotion,
    avgPnL: stats.avg_pnl,
    winRate: stats.win_rate,
    count: stats.count,
    emotionalScore: stats.avg_emotional_score
  }));

  const planComparisonData = planAnalysis ? [
    {
      category: 'Followed Plan',
      avgPnL: planAnalysis.followed_plan.avg_pnl,
      winRate: planAnalysis.followed_plan.win_rate,
      count: planAnalysis.followed_plan.count
    },
    {
      category: 'Broke Plan',
      avgPnL: planAnalysis.broke_plan.avg_pnl,
      winRate: planAnalysis.broke_plan.win_rate,
      count: planAnalysis.broke_plan.count
    }
  ] : [];

  const trendColors = ['#8884d8', '#82ca9d', '#ffc658'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Emotional Analytics Dashboard</h2>
        <p className="text-gray-600">
          Understand how your emotions and psychology impact your trading performance
        </p>
      </div>

      {/* Key Insights */}
      {insights.length > 0 && (
        <div className="bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">🧠 Key Insights</h3>
          <div className="space-y-2">
            {insights.map((insight, index) => (
              <div key={index} className="text-blue-800 bg-white rounded p-3 shadow-sm">
                {insight}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Plan Execution Analysis */}
      {planAnalysis && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📋 Plan Execution Impact</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={planComparisonData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" />
                  <YAxis />
                  <Tooltip formatter={(value, name) => [
                    name === 'avgPnL' ? `$${value.toFixed(2)}` : `${value.toFixed(1)}%`,
                    name === 'avgPnL' ? 'Avg P&L' : 'Win Rate'
                  ]} />
                  <Bar dataKey="avgPnL" fill="#3B82F6" name="avgPnL" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-4">
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-semibold text-green-800">When Following Plan</h4>
                <p className="text-green-700">
                  Average P&L: ${planAnalysis.followed_plan.avg_pnl.toFixed(2)}
                </p>
                <p className="text-green-700">
                  Win Rate: {planAnalysis.followed_plan.win_rate.toFixed(1)}%
                </p>
                <p className="text-green-700">
                  Trades: {planAnalysis.followed_plan.count}
                </p>
              </div>
              <div className="bg-red-50 p-4 rounded-lg">
                <h4 className="font-semibold text-red-800">When Breaking Plan</h4>
                <p className="text-red-700">
                  Average P&L: ${planAnalysis.broke_plan.avg_pnl.toFixed(2)}
                </p>
                <p className="text-red-700">
                  Win Rate: {planAnalysis.broke_plan.win_rate.toFixed(1)}%
                </p>
                <p className="text-red-700">
                  Trades: {planAnalysis.broke_plan.count}
                </p>
              </div>
              {planAnalysis.plan_adherence_impact.pnl_difference > 0 && (
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-blue-800">💡 Impact</h4>
                  <p className="text-blue-700">
                    Following your plan generates ${planAnalysis.plan_adherence_impact.pnl_difference.toFixed(2)} more per trade
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Emotion Performance Correlation */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">😤 Emotion vs Performance</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={emotionChartData.filter(d => d.count >= 3)}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="emotion" angle={-45} textAnchor="end" height={100} />
            <YAxis />
            <Tooltip formatter={(value, name) => [
              name === 'avgPnL' ? `$${value.toFixed(2)}` : `${value.toFixed(1)}%`,
              name === 'avgPnL' ? 'Avg P&L' : 'Win Rate'
            ]} />
            <Bar dataKey="avgPnL" fill="#EF4444" name="avgPnL" />
            <Bar dataKey="winRate" fill="#10B981" name="winRate" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Emotional Trends Over Time */}
      {trends && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📈 Emotional Control Trends</h3>
          <div className="mb-4">
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              trends.overall_improvement.trend === 'improving' ? 'bg-green-100 text-green-800' :
              trends.overall_improvement.trend === 'declining' ? 'bg-red-100 text-red-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {trends.overall_improvement.trend === 'improving' ? '📈 Improving' :
               trends.overall_improvement.trend === 'declining' ? '📉 Declining' :
               '➡️ Stable'}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trends.weekly_trends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="week" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="avg_emotional_score" 
                stroke="#3B82F6" 
                strokeWidth={2}
                name="Emotional Score"
              />
              <Line 
                type="monotone" 
                dataKey="plan_adherence_rate" 
                stroke="#10B981" 
                strokeWidth={2}
                name="Plan Adherence %"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default EmotionalAnalyticsDashboard;
