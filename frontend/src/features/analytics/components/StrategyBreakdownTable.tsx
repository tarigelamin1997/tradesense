
import React from 'react';

interface Strategy {
  name: string;
  total_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_return: number;
  profit_factor: number;
  best_trade: number;
  worst_trade: number;
}

interface StrategyBreakdownTableProps {
  strategies: Strategy[];
}

export const StrategyBreakdownTable: React.FC<StrategyBreakdownTableProps> = ({ strategies }) => {
  if (!strategies.length) {
    return (
      <div className="text-center py-8 text-gray-500">
        No strategy data available
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Strategy
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Trades
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Win Rate
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Total P&L
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Avg Return
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Profit Factor
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Best/Worst
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {strategies.map((strategy, index) => (
            <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm font-medium text-gray-900">{strategy.name}</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {strategy.total_trades}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`text-sm font-medium ${
                  strategy.win_rate >= 60 ? 'text-green-600' : 
                  strategy.win_rate >= 40 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {strategy.win_rate.toFixed(1)}%
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`text-sm font-medium ${
                  strategy.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  ${strategy.total_pnl.toFixed(2)}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`text-sm ${
                  strategy.avg_return >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  ${strategy.avg_return.toFixed(2)}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {strategy.profit_factor.toFixed(2)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <div className="text-green-600">${strategy.best_trade.toFixed(2)}</div>
                <div className="text-red-600">${strategy.worst_trade.toFixed(2)}</div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
