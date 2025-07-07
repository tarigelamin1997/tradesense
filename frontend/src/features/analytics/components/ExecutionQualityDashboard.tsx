
import React, { useState, useEffect } from 'react';
import { Card } from '../../../components/ui/Card';
import { executionQualityService, ExecutionQualityAnalysis, ExecutionMetrics } from '../../../services/executionQuality';

const ExecutionQualityDashboard: React.FC = () => {
  const [data, setData] = useState<ExecutionQualityAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<keyof ExecutionMetrics>('execution_score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    fetchExecutionQuality();
  }, []);

  const fetchExecutionQuality = async () => {
    try {
      setLoading(true);
      const result = await executionQualityService.getExecutionQuality();
      setData(result);
    } catch (err) {
      setError('Failed to load execution quality data');
      console.error('Execution quality error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (column: keyof ExecutionMetrics) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  const sortedTrades = data?.trade_execution_data?.slice().sort((a, b) => {
    const aVal = a[sortBy];
    const bVal = b[sortBy];
    
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
    }
    
    return sortOrder === 'asc' 
      ? String(aVal).localeCompare(String(bVal))
      : String(bVal).localeCompare(String(aVal));
  });

  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getGradeColor = (grade: string): string => {
    if (grade.startsWith('A')) return 'bg-green-100 text-green-800';
    if (grade.startsWith('B')) return 'bg-blue-100 text-blue-800';
    if (grade.startsWith('C')) return 'bg-yellow-100 text-yellow-800';
    if (grade.startsWith('D')) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center text-red-600">
          <p>{error}</p>
          <button 
            onClick={fetchExecutionQuality}
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  if (!data || data.trade_execution_data.length === 0) {
    return (
      <Card className="p-6">
        <div className="text-center text-gray-500">
          <h3 className="text-lg font-semibold mb-2">No Execution Data Available</h3>
          <p>Add trades with complete entry/exit data to begin execution analysis.</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Execution Quality Analysis</h2>
        <p className="text-gray-600">
          Analyze entry timing, exit efficiency, and overall execution quality
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm font-medium text-gray-500">Average Execution Score</div>
          <div className={`text-2xl font-bold ${getScoreColor(data.execution_summary.average_execution_score)}`}>
            {data.execution_summary.average_execution_score}
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="text-sm font-medium text-gray-500">Entry Timing</div>
          <div className={`text-2xl font-bold ${getScoreColor(data.execution_summary.average_entry_score)}`}>
            {data.execution_summary.average_entry_score}
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="text-sm font-medium text-gray-500">Exit Quality</div>
          <div className={`text-2xl font-bold ${getScoreColor(data.execution_summary.average_exit_score)}`}>
            {data.execution_summary.average_exit_score}
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="text-sm font-medium text-gray-500">Execution Consistency</div>
          <div className={`text-2xl font-bold ${getScoreColor(data.execution_summary.execution_consistency)}`}>
            {data.execution_summary.execution_consistency}%
          </div>
        </Card>
      </div>

      {/* Grade Distribution */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Execution Grade Distribution</h3>
        <div className="flex flex-wrap gap-2">
          {Object.entries(data.execution_summary.grade_distribution).map(([grade, count]) => (
            <span
              key={grade}
              className={`px-3 py-1 rounded-full text-sm font-medium ${getGradeColor(grade)}`}
            >
              {grade}: {count}
            </span>
          ))}
        </div>
      </Card>

      {/* Insights */}
      {data.insights.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Key Insights</h3>
          <div className="space-y-2">
            {data.insights.map((insight, index) => (
              <div key={index} className="p-3 bg-blue-50 border-l-4 border-blue-400 text-blue-700">
                {insight}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Recommendations */}
      {data.recommendations.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Recommendations</h3>
          <div className="space-y-2">
            {data.recommendations.map((recommendation, index) => (
              <div key={index} className="p-3 bg-green-50 border-l-4 border-green-400 text-green-700">
                {recommendation}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Detailed Trade Analysis */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Trade-by-Trade Execution Analysis</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('symbol')}
                >
                  Symbol {sortBy === 'symbol' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('execution_score')}
                >
                  Execution Score {sortBy === 'execution_score' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('execution_grade')}
                >
                  Grade {sortBy === 'execution_grade' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('entry_timing_score')}
                >
                  Entry Score {sortBy === 'entry_timing_score' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('exit_quality_score')}
                >
                  Exit Score {sortBy === 'exit_quality_score' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('regret_index')}
                >
                  Regret Index {sortBy === 'regret_index' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Primary Weakness
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('pnl')}
                >
                  P&L {sortBy === 'pnl' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedTrades?.map((trade) => (
                <tr key={trade.trade_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {trade.symbol}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-2 py-1 rounded ${getScoreColor(trade.execution_score)}`}>
                      {trade.execution_score}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getGradeColor(trade.execution_grade)}`}>
                      {trade.execution_grade}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-2 py-1 rounded ${getScoreColor(trade.entry_timing_score)}`}>
                      {trade.entry_timing_score}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-2 py-1 rounded ${getScoreColor(trade.exit_quality_score)}`}>
                      {trade.exit_quality_score}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {trade.regret_index.toFixed(3)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                    {trade.primary_weakness}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`font-medium ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${trade.pnl.toFixed(2)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default ExecutionQualityDashboard;
import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter
} from 'recharts';
import { Card } from '../../../components/ui/Card';
import { executionQualityService, ExecutionQualityResponse } from '../../../services/executionQuality';

const ExecutionQualityDashboard: React.FC = () => {
  const [executionData, setExecutionData] = useState<ExecutionQualityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadExecutionData();
  }, []);

  const loadExecutionData = async () => {
    try {
      setLoading(true);
      const data = await executionQualityService.getExecutionQuality();
      setExecutionData(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load execution quality data');
    } finally {
      setLoading(false);
    }
  };

  const getExecutionOverTimeData = () => {
    if (!executionData) return [];
    
    return executionData.trade_execution_data
      .sort((a, b) => new Date(a.entry_time).getTime() - new Date(b.entry_time).getTime())
      .map((trade, index) => ({
        tradeNumber: index + 1,
        executionScore: trade.execution_score,
        entryScore: trade.entry_score,
        exitScore: trade.exit_score,
        pnl: trade.pnl,
        symbol: trade.symbol,
        date: new Date(trade.entry_time).toLocaleDateString()
      }));
  };

  const getGradeDistributionData = () => {
    if (!executionData?.overall_stats.grade_distribution) return [];
    
    const grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'F'];
    const colors = ['#10B981', '#059669', '#047857', '#FCD34D', '#F59E0B', '#D97706', '#F97316', '#EA580C', '#DC2626', '#B91C1C'];
    
    return grades.map((grade, index) => ({
      grade,
      count: executionData.overall_stats.grade_distribution[grade] || 0,
      fill: colors[index]
    })).filter(item => item.count > 0);
  };

  const getExecutionVsPnLData = () => {
    if (!executionData) return [];
    
    return executionData.trade_execution_data.map(trade => ({
      executionScore: trade.execution_score,
      pnl: trade.pnl,
      symbol: trade.symbol,
      grade: trade.execution_grade
    }));
  };

  const getScoreColor = (score: number) => {
    if (score >= 85) return '#10B981';
    if (score >= 70) return '#F59E0B';
    return '#EF4444';
  };

  if (loading) return <div className="p-6">Loading execution quality analysis...</div>;
  if (error) return <div className="p-6 text-red-600">Error: {error}</div>;
  if (!executionData) return <div className="p-6">No execution data available</div>;

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Execution Quality Analysis</h1>
        <div className="text-sm text-gray-600">
          {executionData.total_trades_analyzed} trades analyzed
        </div>
      </div>

      {/* Overall Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">Average Execution Score</h3>
          <div 
            className="text-2xl font-bold"
            style={{ color: getScoreColor(executionData.overall_stats.avg_execution_score) }}
          >
            {executionData.overall_stats.avg_execution_score}
          </div>
          <div className="text-xs text-gray-400">
            ±{executionData.overall_stats.execution_score_std} std dev
          </div>
        </Card>
        
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">Entry vs Exit</h3>
          <div className="flex space-x-2">
            <div className="text-lg font-semibold">
              {executionData.overall_stats.avg_entry_score}
            </div>
            <div className="text-gray-400">vs</div>
            <div className="text-lg font-semibold">
              {executionData.overall_stats.avg_exit_score}
            </div>
          </div>
          <div className="text-xs text-gray-400">Entry vs Exit Score</div>
        </Card>
        
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">Excellent Executions</h3>
          <div className="text-2xl font-bold text-green-600">
            {executionData.overall_stats.excellent_executions}
          </div>
          <div className="text-xs text-gray-400">
            Score ≥ 85
          </div>
        </Card>

        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">Poor Executions</h3>
          <div className="text-2xl font-bold text-red-600">
            {executionData.overall_stats.poor_executions}
          </div>
          <div className="text-xs text-gray-400">
            Score < 60
          </div>
        </Card>
      </div>

      {/* Insights */}
      {executionData.insights.length > 0 && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">🎯 Execution Insights</h2>
          <div className="space-y-2">
            {executionData.insights.map((insight, index) => (
              <div 
                key={index} 
                className={`p-3 rounded-lg ${
                  insight.includes('⚠️') ? 'bg-yellow-50 border-l-4 border-yellow-400' :
                  insight.includes('✅') ? 'bg-green-50 border-l-4 border-green-400' :
                  'bg-blue-50 border-l-4 border-blue-400'
                }`}
              >
                {insight}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Execution Score Over Time */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Execution Score Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={getExecutionOverTimeData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="tradeNumber" 
                label={{ value: 'Trade Number', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                domain={[0, 100]}
                label={{ value: 'Score', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                formatter={(value, name) => [value, name === 'executionScore' ? 'Execution Score' : name]}
                labelFormatter={(value) => `Trade #${value}`}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="executionScore" 
                stroke="#3B82F6" 
                strokeWidth={2}
                name="Execution Score"
                dot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* Grade Distribution */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Execution Grade Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={getGradeDistributionData()}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ grade, count }) => `${grade}: ${count}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {getGradeDistributionData().map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* Execution Score vs PnL */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Execution Score vs P&L</h2>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart data={getExecutionVsPnLData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="executionScore" 
                domain={[0, 100]}
                label={{ value: 'Execution Score', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                dataKey="pnl"
                label={{ value: 'P&L ($)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                formatter={(value, name) => [
                  name === 'pnl' ? `$${value}` : value,
                  name === 'pnl' ? 'P&L' : 'Execution Score'
                ]}
              />
              <Scatter 
                dataKey="pnl" 
                fill="#3B82F6"
                shape="circle"
              />
            </ScatterChart>
          </ResponsiveContainer>
        </Card>

        {/* Entry vs Exit Scores */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Entry vs Exit Performance</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getExecutionOverTimeData().slice(-20)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="tradeNumber" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Bar dataKey="entryScore" fill="#10B981" name="Entry Score" />
              <Bar dataKey="exitScore" fill="#F59E0B" name="Exit Score" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Detailed Trade Table */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Recent Trade Execution Details</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entry Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Exit Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Execution Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Grade
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {executionData.trade_execution_data.slice(-10).reverse().map((trade, index) => (
                <tr key={trade.trade_id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {trade.symbol}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(trade.entry_time).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                      ${trade.pnl}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span style={{ color: getScoreColor(trade.entry_score) }}>
                      {trade.entry_score}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span style={{ color: getScoreColor(trade.exit_score) }}>
                      {trade.exit_score}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span style={{ color: getScoreColor(trade.execution_score) }}>
                      {trade.execution_score}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <span 
                      className={`px-2 py-1 rounded-full text-xs ${
                        trade.execution_grade.startsWith('A') ? 'bg-green-100 text-green-800' :
                        trade.execution_grade.startsWith('B') ? 'bg-yellow-100 text-yellow-800' :
                        trade.execution_grade.startsWith('C') ? 'bg-orange-100 text-orange-800' :
                        'bg-red-100 text-red-800'
                      }`}
                    >
                      {trade.execution_grade}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default ExecutionQualityDashboard;
