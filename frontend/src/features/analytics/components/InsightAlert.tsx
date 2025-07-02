
import React from 'react';

interface InsightAlertProps {
  type: 'success' | 'warning' | 'info' | 'error';
  message: string;
}

const alertStyles = {
  success: 'bg-green-50 border-green-200 text-green-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
  error: 'bg-red-50 border-red-200 text-red-800'
};

const alertIcons = {
  success: '✅',
  warning: '⚠️',
  info: 'ℹ️',
  error: '❌'
};

export const InsightAlert: React.FC<InsightAlertProps> = ({ type, message }) => {
  const alertClass = alertStyles[type];
  const icon = alertIcons[type];

  return (
    <div className={`border rounded-md p-3 ${alertClass}`}>
      <div className="flex items-center space-x-2">
        <span>{icon}</span>
        <p className="text-sm font-medium">{message}</p>
      </div>
    </div>
  );
};
