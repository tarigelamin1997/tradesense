
import React, { useState, useEffect } from 'react';
import { Line, Bar } from 'react-chartjs-2';
import { Card } from '../../../components/ui/Card';

interface CalibrationData {
  confidence_range: string;
  expected_confidence: number;
  actual_win_rate: number;
  calibration_error: number;
  trade_count: number;
  avg_pnl: number;
}

interface ConfidenceCalibrationProps {
  userId: number;
}

export const ConfidenceCalibrationChart: React.FC<ConfidenceCalibrationProps> = ({ userId }) => {
  const [calibrationData, setCalibrationData] = useState<CalibrationData[]>([]);
  const [overallScore, setOverallScore] = useState<number>(0);
  const [insights, setInsights] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCalibrationData();
  }, [userId]);

  const fetchCalibrationData = async () => {
    try {
      const response = await fetch(`/api/v1/analytics/confidence-calibration/${userId}`);
      const data = await response.json();
      
      if (data.calibration_data) {
        setCalibrationData(data.calibration_data);
        setOverallScore(data.overall_calibration_score);
        setInsights(data.insights || []);
      }
    } catch (error) {
      console.error('Error fetching calibration data:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartData = {
    labels: calibrationData.map(d => d.confidence_range),
    datasets: [
      {
        label: 'Expected Confidence %',
        data: calibrationData.map(d => d.expected_confidence),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.1
      },
      {
        label: 'Actual Win Rate %',
        data: calibrationData.map(d => d.actual_win_rate),
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.1
      }
    ]
  };

  const options = {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: 'Confidence Calibration Analysis'
      },
      legend: {
        position: 'top' as const,
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        title: {
          display: true,
          text: 'Percentage'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Confidence Range'
        }
      }
    }
  };

  if (loading) return <div>Loading confidence analysis...</div>;

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold">Confidence Calibration</h3>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            overallScore > 85 ? 'bg-green-100 text-green-800' :
            overallScore > 70 ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>
            Score: {overallScore}%
          </div>
        </div>
        
        <div className="h-96">
          <Line data={chartData} options={options} />
        </div>
      </Card>

      <Card className="p-6">
        <h4 className="text-lg font-semibold mb-3">Calibration Insights</h4>
        <div className="space-y-2">
          {insights.map((insight, index) => (
            <div key={index} className="p-3 bg-blue-50 rounded-lg">
              {insight}
            </div>
          ))}
        </div>
      </Card>

      <Card className="p-6">
        <h4 className="text-lg font-semibold mb-3">Detailed Breakdown</h4>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Confidence Range
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Expected
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actual
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Error
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trades
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {calibrationData.map((row, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {row.confidence_range}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {row.expected_confidence.toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {row.actual_win_rate.toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {row.calibration_error.toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {row.trade_count}
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
