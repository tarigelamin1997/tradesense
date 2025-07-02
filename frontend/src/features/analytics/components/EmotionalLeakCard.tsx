
import React from 'react';
import { Card } from '../../../components/ui/Card';

interface EmotionalLeak {
  category: string;
  name: string;
  cost: number;
  frequency: number;
  description: string;
  severity: string;
}

interface EmotionalLeakCardProps {
  leak: EmotionalLeak;
}

const severityColors = {
  low: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  medium: 'bg-orange-50 border-orange-200 text-orange-800',
  high: 'bg-red-50 border-red-200 text-red-800',
  critical: 'bg-red-100 border-red-300 text-red-900'
};

const severityIcons = {
  low: '⚠️',
  medium: '🚨',
  high: '🔥',
  critical: '💥'
};

export const EmotionalLeakCard: React.FC<EmotionalLeakCardProps> = ({ leak }) => {
  const severityClass = severityColors[leak.severity as keyof typeof severityColors] || severityColors.medium;
  const severityIcon = severityIcons[leak.severity as keyof typeof severityIcons] || '⚠️';

  return (
    <Card className={`p-4 border-l-4 ${severityClass}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-xl">{severityIcon}</span>
          <div>
            <h4 className="font-semibold">{leak.name}</h4>
            <p className="text-sm opacity-75 capitalize">{leak.category}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="font-bold text-lg">-${leak.cost.toFixed(0)}</p>
          <p className="text-xs opacity-75">{leak.frequency} times</p>
        </div>
      </div>
      <p className="mt-2 text-sm">{leak.description}</p>
      <div className="mt-2 flex justify-between items-center">
        <span className={`px-2 py-1 rounded text-xs font-medium uppercase ${severityClass}`}>
          {leak.severity}
        </span>
        <span className="text-xs opacity-75">
          ${(leak.cost / leak.frequency).toFixed(0)} avg per occurrence
        </span>
      </div>
    </Card>
  );
};
