
import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui';
import { formatPercentage } from '../../../utils/formatters';

interface WinRateGaugeProps {
  winRate: number;
}

export const WinRateGauge: React.FC<WinRateGaugeProps> = ({ winRate }) => {
  const data = [
    { name: 'Win Rate', value: winRate, fill: '#10B981' },
    { name: 'Loss Rate', value: 100 - winRate, fill: '#EF4444' }
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Win Rate Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip formatter={(value: number) => formatPercentage(value)} />
          </PieChart>
        </ResponsiveContainer>
        <div className="text-center mt-4">
          <p className="text-2xl font-bold text-gray-900">{formatPercentage(winRate)}</p>
          <p className="text-sm text-gray-600">Overall Win Rate</p>
        </div>
      </CardContent>
    </Card>
  );
};
