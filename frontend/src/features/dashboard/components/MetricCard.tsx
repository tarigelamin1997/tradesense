
import React from 'react';
import { TrendingUpIcon, TrendingDownIcon } from '@heroicons/react/24/outline';
import { Card } from '../../../components/ui';
import { formatCurrency, formatPercentage } from '../../../utils/formatters';

interface MetricCardProps {
  title: string;
  value: number;
  change?: number;
  icon: React.ComponentType<{ className?: string }>;
  trend?: 'up' | 'down' | 'neutral';
  format?: 'currency' | 'percentage' | 'number';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  icon: Icon,
  trend = 'neutral',
  format = 'number'
}) => {
  const formatValue = (val: number) => {
    switch (format) {
      case 'currency':
        return formatCurrency(val);
      case 'percentage':
        return formatPercentage(val);
      default:
        return val.toLocaleString();
    }
  };

  const trendColor = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-blue-600'
  };

  const trendBg = {
    up: 'bg-green-100',
    down: 'bg-red-100',
    neutral: 'bg-blue-100'
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${trendBg[trend]}`}>
            <Icon className={`h-6 w-6 ${trendColor[trend]}`} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{formatValue(value)}</p>
          </div>
        </div>
        {change !== undefined && (
          <div className={`flex items-center space-x-1 ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {change >= 0 ? (
              <TrendingUpIcon className="h-4 w-4" />
            ) : (
              <TrendingDownIcon className="h-4 w-4" />
            )}
            <span className="text-sm font-medium">
              {change >= 0 ? '+' : ''}{formatPercentage(change)}
            </span>
          </div>
        )}
      </div>
    </Card>
  );
};
