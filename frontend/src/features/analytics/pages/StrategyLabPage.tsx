
import React from 'react';
import StrategyLabDashboard from '../components/StrategyLabDashboard';

const StrategyLabPage: React.FC = () => {
  return (
    <div className="strategy-lab-page">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Strategy Lab</h1>
        <p className="mt-2 text-gray-600">
          Audit your trading decisions and discover which rules and behaviors actually improve your performance.
          This is not backtesting - it's decision auditing using your real trade data.
        </p>
      </div>
      
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-blue-900 mb-2">💡 Strategy Lab Insights</h3>
        <ul className="text-blue-800 text-sm space-y-1">
          <li>• <strong>Simulator:</strong> Test how following specific criteria would have affected your results</li>
          <li>• <strong>Playbook Analysis:</strong> Compare performance across your different trading strategies</li>
          <li>• <strong>What-If Scenarios:</strong> See automated analyses of common improvements</li>
          <li>• <strong>Decision Auditing:</strong> Focus on your behavior, not market predictions</li>
        </ul>
      </div>

      <StrategyLabDashboard />
    </div>
  );
};

export default StrategyLabPage;
