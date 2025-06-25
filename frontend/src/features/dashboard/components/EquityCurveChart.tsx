
import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui';
import { formatCurrency } from '../../../utils/formatters';

interface EquityCurveData {
  date: string;
  cumulativePnL: number;
}

interface EquityCurveChartProps {
  data: EquityCurveData[];
}

export const EquityCurveChart: React.FC<EquityCurveChartProps> = ({ data }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Equity Curve</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip 
              formatter={(value: number) => [formatCurrency(value), 'Cumulative P&L']}
              labelFormatter={(label) => `Trade: ${label}`}
            />
            <Area 
              type="monotone" 
              dataKey="cumulativePnL" 
              stroke="#3B82F6" 
              fill="#3B82F6" 
              fillOpacity={0.2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};
