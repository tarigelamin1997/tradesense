
import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { Card } from '../../../components/ui/Card';
import { confidenceCalibrationService, ConfidenceCalibrationResponse } from '../../../services/confidenceCalibration';

const ConfidenceCalibrationDashboard: React.FC = () => {
  const [calibrationData, setCalibrationData] = useState<ConfidenceCalibrationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCalibrationData();
  }, []);

  const loadCalibrationData = async () => {
    try {
      setLoading(true);
      const data = await confidenceCalibrationService.getConfidenceCalibration();
      setCalibrationData(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load confidence calibration data');
    } finally {
      setLoading(false);
    }
  };

  const getCalibrationCurveData = () => {
    if (!calibrationData) return [];
    
    return calibrationData.calibration_data.map(bin => ({
      confidence: bin.confidence_midpoint,
      winRate: bin.win_rate,
      perfectCalibration: bin.confidence_midpoint,
      totalTrades: bin.total_trades
    }));
  };

  const getPnLByConfidenceData = () => {
    if (!calibrationData) return [];
    
    return calibrationData.calibration_data.map(bin => ({
      range: bin.confidence_range,
      avgPnL: bin.avg_pnl,
      totalTrades: bin.total_trades,
      winRate: bin.win_rate
    }));
  };

  const getCorrelationColor = (correlation: number) => {
    if (correlation > 0.3) return '#10B981'; // Green
    if (correlation < -0.3) return '#EF4444'; // Red
    return '#F59E0B'; // Yellow
  };

  if (loading) return <div className="p-6">Loading confidence calibration analysis...</div>;
  if (error) return <div className="p-6 text-red-600">Error: {error}</div>;
  if (!calibrationData) return <div className="p-6">No data available</div>;

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Confidence Calibration Analysis</h1>
        <div className="text-sm text-gray-600">
          {calibrationData.total_trades_analyzed} trades analyzed
        </div>
      </div>

      {/* Overall Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">Average Confidence</h3>
          <div className="text-2xl font-bold">
            {calibrationData.overall_stats.avg_confidence}%
          </div>
        </Card>
        
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">Confidence Range</h3>
          <div className="text-2xl font-bold">
            ±{calibrationData.overall_stats.confidence_std}%
          </div>
        </Card>
        
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">Confidence-PnL Correlation</h3>
          <div 
            className="text-2xl font-bold"
            style={{ color: getCorrelationColor(calibrationData.overall_stats.confidence_pnl_correlation) }}
          >
            {calibrationData.overall_stats.confidence_pnl_correlation}
          </div>
        </Card>

        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">Calibration Quality</h3>
          <div className="text-sm font-medium">
            {calibrationData.overall_stats.correlation_interpretation}
          </div>
        </Card>
      </div>

      {/* Insights */}
      {calibrationData.insights.length > 0 && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">🎯 Key Insights</h2>
          <div className="space-y-2">
            {calibrationData.insights.map((insight, index) => (
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

      {/* Calibration Curve */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Confidence vs Reality Calibration Curve</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={getCalibrationCurveData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="confidence" 
                label={{ value: 'Confidence Level (%)', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                label={{ value: 'Win Rate (%)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                formatter={(value, name) => [
                  `${value}%`, 
                  name === 'winRate' ? 'Actual Win Rate' : 'Perfect Calibration'
                ]}
                labelFormatter={(value) => `Confidence: ${value}%`}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="perfectCalibration" 
                stroke="#94A3B8" 
                strokeDasharray="5 5"
                name="Perfect Calibration"
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="winRate" 
                stroke="#3B82F6" 
                strokeWidth={2}
                name="Actual Win Rate"
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* PnL by Confidence */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Average PnL by Confidence Level</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getPnLByConfidenceData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" />
              <YAxis 
                label={{ value: 'Avg PnL ($)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                formatter={(value, name) => {
                  if (name === 'avgPnL') return [`$${value}`, 'Average PnL'];
                  if (name === 'totalTrades') return [value, 'Total Trades'];
                  return [value, name];
                }}
              />
              <Bar dataKey="avgPnL" name="Average PnL">
                {getPnLByConfidenceData().map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.avgPnL >= 0 ? '#10B981' : '#EF4444'} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Detailed Breakdown Table */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Detailed Confidence Breakdown</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Confidence Range
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trades
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Win Rate
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg PnL
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Profit Factor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total PnL
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {calibrationData.calibration_data.map((bin, index) => (
                <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {bin.confidence_range}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {bin.total_trades}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={bin.win_rate >= 50 ? 'text-green-600' : 'text-red-600'}>
                      {bin.win_rate}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={bin.avg_pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                      ${bin.avg_pnl}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {bin.profit_factor}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={bin.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                      ${bin.total_pnl}
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

export default ConfidenceCalibrationDashboard;
