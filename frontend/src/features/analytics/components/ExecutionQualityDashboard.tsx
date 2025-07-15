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
      setError(err.message || 'Failed to load execution quality data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        Error: {error}
      </div>
    );
  }

  if (!executionData) {
    return <div>No execution data available</div>;
  }

  const {
    summary,
    price_impact_by_size,
    timing_analysis,
    venue_analysis,
    slippage_patterns
  } = executionData;

  // Colors for charts
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Execution Quality Dashboard</h1>
        <button
          onClick={loadExecutionData}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
            Avg Fill Rate
          </h3>
          <p className="text-2xl font-bold text-gray-900">
            {(summary.avg_fill_rate * 100).toFixed(2)}%
          </p>
        </Card>
        
        <Card>
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
            Avg Slippage
          </h3>
          <p className="text-2xl font-bold text-gray-900">
            {summary.avg_slippage.toFixed(4)}%
          </p>
        </Card>
        
        <Card>
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
            Avg Price Impact
          </h3>
          <p className="text-2xl font-bold text-gray-900">
            {summary.avg_price_impact.toFixed(4)}%
          </p>
        </Card>
        
        <Card>
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
            Total Trades
          </h3>
          <p className="text-2xl font-bold text-gray-900">
            {summary.total_trades}
          </p>
        </Card>
      </div>

      {/* Price Impact by Size */}
      <Card>
        <h2 className="text-lg font-semibold mb-4">Price Impact by Order Size</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={price_impact_by_size}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="size_category" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="avg_impact" fill="#8884d8" name="Avg Impact %" />
            <Bar dataKey="trade_count" fill="#82ca9d" name="Trade Count" />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Timing Analysis */}
      <Card>
        <h2 className="text-lg font-semibold mb-4">Execution Timing Analysis</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={timing_analysis}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="avg_fill_time" 
              stroke="#8884d8" 
              name="Avg Fill Time (s)"
            />
            <Line 
              type="monotone" 
              dataKey="avg_slippage" 
              stroke="#82ca9d" 
              name="Avg Slippage %"
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* Venue Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-lg font-semibold mb-4">Execution by Venue</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={venue_analysis}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ venue, percentage }) => `${venue}: ${percentage.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="trade_count"
              >
                {venue_analysis.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold mb-4">Slippage Patterns</h2>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid />
              <XAxis dataKey="volume" name="Volume" />
              <YAxis dataKey="slippage" name="Slippage %" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter name="Trades" data={slippage_patterns} fill="#8884d8" />
            </ScatterChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Detailed Venue Stats */}
      <Card>
        <h2 className="text-lg font-semibold mb-4">Venue Performance Details</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Venue
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trade Count
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Fill Rate
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Slippage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Fill Time
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {venue_analysis.map((venue, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {venue.venue}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {venue.trade_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {(venue.avg_fill_rate * 100).toFixed(2)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {venue.avg_slippage.toFixed(4)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {venue.avg_fill_time.toFixed(2)}s
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