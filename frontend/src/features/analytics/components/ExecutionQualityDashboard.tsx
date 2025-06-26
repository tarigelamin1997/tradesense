
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
