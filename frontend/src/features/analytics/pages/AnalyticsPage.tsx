
import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, LineChart, Line, ResponsiveContainer,
  ScatterChart, Scatter
} from 'recharts';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { analyticsService } from '../../../services/analytics';
import { EmotionalLeakCard } from '../components/EmotionalLeakCard';
import { InsightAlert } from '../components/InsightAlert';
import { StrategyBreakdownTable } from '../components/StrategyBreakdownTable';
import { ConfidenceHeatmap } from '../components/ConfidenceHeatmap';

interface AnalyticsSummary {
  total_trades: number;
  total_pnl: number;
  overall_win_rate: number;
  strategy_stats: Array<{
    name: string;
    total_trades: number;
    win_rate: number;
    total_pnl: number;
    avg_return: number;
  }>;
  emotion_impact: Array<{
    emotion: string;
    trade_count: number;
    win_rate: number;
    net_pnl: number;
    impact_score: number;
  }>;
  trigger_analysis: Array<{
    trigger: string;
    usage_count: number;
    win_rate: number;
    net_result: number;
  }>;
  confidence_analysis: Array<{
    confidence_level: number;
    trade_count: number;
    win_rate: number;
    avg_pnl: number;
  }>;
  emotional_leaks: Array<{
    category: string;
    name: string;
    cost: number;
    frequency: number;
    description: string;
    severity: string;
  }>;
  most_profitable_emotion: string;
  most_costly_emotion: string;
  hesitation_cost: number;
  fomo_impact: number;
  revenge_trading_cost: number;
  confidence_vs_performance_correlation: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export const AnalyticsPage: React.FC = () => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateFilter, setDateFilter] = useState<{start?: string, end?: string}>({});

  useEffect(() => {
    loadAnalytics();
  }, [dateFilter]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const data = await analyticsService.getSummary(dateFilter);
      setSummary(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-800">Error loading analytics: {error}</p>
        <Button onClick={loadAnalytics} className="mt-2">Retry</Button>
      </div>
    );
  }

  if (!summary) return null;

  // Prepare chart data
  const emotionChartData = summary.emotion_impact.map(e => ({
    emotion: e.emotion,
    impact: e.net_pnl,
    trades: e.trade_count,
    winRate: e.win_rate
  }));

  const triggerChartData = summary.trigger_analysis.map(t => ({
    trigger: t.trigger,
    usage: t.usage_count,
    result: t.net_result,
    winRate: t.win_rate
  }));

  const confidenceChartData = summary.confidence_analysis.map(c => ({
    confidence: c.confidence_level,
    winRate: c.win_rate,
    avgPnL: c.avg_pnl,
    trades: c.trade_count
  }));

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Trading Analytics</h1>
          <p className="text-gray-600">Insights into your trading performance and behavior</p>
        </div>
        <div className="flex space-x-2">
          <input
            type="date"
            value={dateFilter.start || ''}
            onChange={(e) => setDateFilter(prev => ({...prev, start: e.target.value}))}
            className="px-3 py-2 border border-gray-300 rounded-md"
          />
          <input
            type="date"
            value={dateFilter.end || ''}
            onChange={(e) => setDateFilter(prev => ({...prev, end: e.target.value}))}
            className="px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">Total Trades</h3>
          <p className="text-2xl font-bold text-gray-900">{summary.total_trades}</p>
        </Card>
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">Total P&L</h3>
          <p className={`text-2xl font-bold ${summary.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            ${summary.total_pnl.toFixed(2)}
          </p>
        </Card>
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">Win Rate</h3>
          <p className="text-2xl font-bold text-gray-900">{summary.overall_win_rate.toFixed(1)}%</p>
        </Card>
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">Emotional Cost</h3>
          <p className="text-2xl font-bold text-red-600">
            ${(summary.hesitation_cost + Math.abs(summary.fomo_impact) + summary.revenge_trading_cost).toFixed(0)}
          </p>
        </Card>
      </div>

      {/* Emotional Leaks Section */}
      {summary.emotional_leaks.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">🚨 Emotional Leaks</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {summary.emotional_leaks.map((leak, index) => (
              <EmotionalLeakCard key={index} leak={leak} />
            ))}
          </div>
        </div>
      )}

      {/* Key Insights */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-900">💡 Key Insights</h2>
        <div className="space-y-2">
          {summary.most_costly_emotion && (
            <InsightAlert
              type="warning"
              message={`Your most costly emotion is "${summary.most_costly_emotion}" - consider developing strategies to manage this state.`}
            />
          )}
          {summary.most_profitable_emotion && (
            <InsightAlert
              type="success"
              message={`You perform best when "${summary.most_profitable_emotion}" - try to cultivate this mindset.`}
            />
          )}
          {summary.confidence_vs_performance_correlation < 0 && (
            <InsightAlert
              type="warning"
              message={`Your confidence negatively correlates with performance (${summary.confidence_vs_performance_correlation.toFixed(2)}) - you may be overconfident on losing trades.`}
            />
          )}
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Strategy Performance */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Strategy Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={summary.strategy_stats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="total_pnl" fill="#8884d8" name="Total P&L" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Emotion Impact */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Emotion Impact on P&L</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={emotionChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="emotion" />
              <YAxis />
              <Tooltip />
              <Bar 
                dataKey="impact" 
                fill={(entry: any) => entry.impact >= 0 ? '#00C49F' : '#FF8042'}
                name="P&L Impact"
              />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Trigger Analysis */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Mental Trigger Usage</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={triggerChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ trigger, usage }) => `${trigger}: ${usage}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="usage"
              >
                {triggerChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* Confidence vs Performance */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Confidence vs Win Rate</h3>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart data={confidenceChartData}>
              <CartesianGrid />
              <XAxis dataKey="confidence" name="Confidence" />
              <YAxis dataKey="winRate" name="Win Rate" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter name="Confidence vs Win Rate" data={confidenceChartData} fill="#8884d8" />
            </ScatterChart>
          </ResponsiveContainer>
        </Card>

      </div>

      {/* Strategy Breakdown Table */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Detailed Strategy Breakdown</h3>
        <StrategyBreakdownTable strategies={summary.strategy_stats} />
      </Card>

    </div>
  );
};
