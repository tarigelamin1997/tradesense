
import React, { useState, useEffect } from 'react';
import { heatmapService, HeatmapData, TimeSlot, SymbolStats } from '../../../services/heatmap';

interface PerformanceHeatmapProps {
  startDate?: string;
  endDate?: string;
}

const PerformanceHeatmap: React.FC<PerformanceHeatmapProps> = ({
  startDate,
  endDate
}) => {
  const [heatmapData, setHeatmapData] = useState<HeatmapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'time' | 'symbols'>('time');

  useEffect(() => {
    loadHeatmapData();
  }, [startDate, endDate]);

  const loadHeatmapData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await heatmapService.getPerformanceHeatmap(startDate, endDate);
      setHeatmapData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load heatmap data');
    } finally {
      setLoading(false);
    }
  };

  const getPnlColor = (pnl: number, maxAbsPnl: number): string => {
    if (pnl === 0) return 'bg-gray-100';
    
    const intensity = Math.abs(pnl) / maxAbsPnl;
    const alpha = Math.min(intensity * 0.8 + 0.2, 1);
    
    if (pnl > 0) {
      return `bg-green-500 bg-opacity-${Math.round(alpha * 100)}`;
    } else {
      return `bg-red-500 bg-opacity-${Math.round(alpha * 100)}`;
    }
  };

  const formatHour = (hour: number): string => {
    return `${hour.toString().padStart(2, '0')}:00`;
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <div className="text-red-600 mr-3">⚠️</div>
          <div>
            <h3 className="text-red-800 font-semibold">Error Loading Heatmap</h3>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
        <button
          onClick={loadHeatmapData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!heatmapData) {
    return (
      <div className="text-center p-8">
        <p className="text-gray-500">No heatmap data available</p>
      </div>
    );
  }

  const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const hours = Array.from({ length: 24 }, (_, i) => i);

  // Calculate max absolute PnL for color scaling
  const allPnlValues = weekdays.flatMap(day => 
    heatmapData.time_heatmap.avg_pnl_matrix[day] || []
  );
  const maxAbsPnl = Math.max(...allPnlValues.map(Math.abs));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">📊 Performance Heatmap</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveView('time')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeView === 'time'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            🕒 Time Analysis
          </button>
          <button
            onClick={() => setActiveView('symbols')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeView === 'symbols'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            📈 Symbol Performance
          </button>
        </div>
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-blue-600 text-sm font-medium">Total Trades</div>
          <div className="text-2xl font-bold text-blue-900">
            {heatmapData.metadata.total_trades.toLocaleString()}
          </div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="text-green-600 text-sm font-medium">Symbols Analyzed</div>
          <div className="text-2xl font-bold text-green-900">
            {heatmapData.metadata.symbols_analyzed}
          </div>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <div className="text-purple-600 text-sm font-medium">Trading Hours</div>
          <div className="text-2xl font-bold text-purple-900">
            {heatmapData.time_heatmap.total_trading_hours}
          </div>
        </div>
        <div className="bg-orange-50 p-4 rounded-lg">
          <div className="text-orange-600 text-sm font-medium">Date Range</div>
          <div className="text-sm font-semibold text-orange-900">
            {heatmapData.metadata.date_range.start 
              ? new Date(heatmapData.metadata.date_range.start).toLocaleDateString()
              : 'N/A'
            } - {heatmapData.metadata.date_range.end 
              ? new Date(heatmapData.metadata.date_range.end).toLocaleDateString()
              : 'N/A'
            }
          </div>
        </div>
      </div>

      {/* Time Heatmap View */}
      {activeView === 'time' && (
        <div className="space-y-6">
          {/* Time Heatmap Grid */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold mb-4">🕒 Performance by Hour & Weekday</h3>
            
            {/* Legend */}
            <div className="flex items-center justify-center mb-4 space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-red-500 rounded"></div>
                <span className="text-sm text-gray-600">Losses</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-gray-100 rounded"></div>
                <span className="text-sm text-gray-600">Neutral</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-green-500 rounded"></div>
                <span className="text-sm text-gray-600">Profits</span>
              </div>
            </div>

            {/* Heatmap Grid */}
            <div className="overflow-x-auto">
              <div className="min-w-max">
                {/* Hour headers */}
                <div className="flex mb-2">
                  <div className="w-20"></div>
                  {hours.map(hour => (
                    <div key={hour} className="w-8 text-xs text-center text-gray-500">
                      {hour % 4 === 0 ? formatHour(hour) : ''}
                    </div>
                  ))}
                </div>

                {/* Grid rows */}
                {weekdays.map(weekday => (
                  <div key={weekday} className="flex items-center mb-1">
                    <div className="w-20 text-sm font-medium text-gray-700 pr-2">
                      {weekday.slice(0, 3)}
                    </div>
                    {hours.map(hour => {
                      const avgPnl = heatmapData.time_heatmap.avg_pnl_matrix[weekday]?.[hour] || 0;
                      const tradeCount = heatmapData.time_heatmap.trade_count_matrix[weekday]?.[hour] || 0;
                      const winRate = heatmapData.time_heatmap.win_rate_matrix[weekday]?.[hour] || 0;
                      
                      return (
                        <div
                          key={hour}
                          className={`w-8 h-8 border border-gray-200 cursor-pointer relative group ${
                            tradeCount > 0 ? getPnlColor(avgPnl, maxAbsPnl) : 'bg-gray-50'
                          }`}
                          title={`${weekday} ${formatHour(hour)}\nTrades: ${tradeCount}\nAvg P&L: ${formatCurrency(avgPnl)}\nWin Rate: ${winRate.toFixed(1)}%`}
                        >
                          {/* Tooltip */}
                          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-black text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 whitespace-nowrap">
                            <div>{weekday} {formatHour(hour)}</div>
                            <div>Trades: {tradeCount}</div>
                            <div>Avg P&L: {formatCurrency(avgPnl)}</div>
                            <div>Win Rate: {winRate.toFixed(1)}%</div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Best/Worst Time Slots */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Best Time Slots */}
            <div className="bg-green-50 p-6 rounded-lg border border-green-200">
              <h3 className="text-lg font-semibold text-green-800 mb-4">🏆 Best Time Slots</h3>
              {heatmapData.time_heatmap.best_time_slots.slice(0, 5).map((slot, index) => (
                <div key={index} className="flex justify-between items-center py-2 border-b border-green-200 last:border-b-0">
                  <div>
                    <div className="font-medium text-green-900">
                      {slot.weekday} {formatHour(slot.hour)}
                    </div>
                    <div className="text-sm text-green-700">
                      {slot.trade_count} trades • {slot.win_rate.toFixed(1)}% win rate
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-green-900">
                      {formatCurrency(slot.avg_pnl)}
                    </div>
                    <div className="text-sm text-green-700">avg</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Worst Time Slots */}
            <div className="bg-red-50 p-6 rounded-lg border border-red-200">
              <h3 className="text-lg font-semibold text-red-800 mb-4">⚠️ Worst Time Slots</h3>
              {heatmapData.time_heatmap.worst_time_slots.slice(0, 5).map((slot, index) => (
                <div key={index} className="flex justify-between items-center py-2 border-b border-red-200 last:border-b-0">
                  <div>
                    <div className="font-medium text-red-900">
                      {slot.weekday} {formatHour(slot.hour)}
                    </div>
                    <div className="text-sm text-red-700">
                      {slot.trade_count} trades • {slot.win_rate.toFixed(1)}% win rate
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-red-900">
                      {formatCurrency(slot.avg_pnl)}
                    </div>
                    <div className="text-sm text-red-700">avg</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Symbol Performance View */}
      {activeView === 'symbols' && (
        <div className="space-y-6">
          {/* Symbol Stats Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-green-600 text-sm font-medium">Profitable Symbols</div>
              <div className="text-2xl font-bold text-green-900">
                {heatmapData.symbol_stats.summary.profitable_symbols} / {heatmapData.symbol_stats.summary.total_symbols}
              </div>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-blue-600 text-sm font-medium">Best Symbol</div>
              <div className="text-xl font-bold text-blue-900">
                {heatmapData.symbol_stats.summary.best_symbol || 'N/A'}
              </div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-purple-600 text-sm font-medium">Most Traded</div>
              <div className="text-xl font-bold text-purple-900">
                {heatmapData.symbol_stats.summary.most_traded_symbol || 'N/A'}
              </div>
            </div>
          </div>

          {/* Symbol Performance Table */}
          <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
            <div className="px-6 py-4 border-b">
              <h3 className="text-lg font-semibold">📈 Symbol Performance Breakdown</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Symbol
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Trades
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total P&L
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Avg P&L
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Win Rate
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Profit Factor
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Consistency
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {heatmapData.symbol_stats.symbols.map((symbol) => (
                    <tr key={symbol.symbol} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="font-medium text-gray-900">{symbol.symbol}</div>
                          <div className="ml-2 text-xs text-gray-500">
                            {symbol.direction_bias}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {symbol.total_trades}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`text-sm font-medium ${
                          symbol.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatCurrency(symbol.total_pnl)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`text-sm font-medium ${
                          symbol.avg_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatCurrency(symbol.avg_pnl)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {symbol.win_rate.toFixed(1)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {symbol.profit_factor === 999 ? '∞' : symbol.profit_factor.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${symbol.consistency_score}%` }}
                          ></div>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {symbol.consistency_score.toFixed(0)}%
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Insights and Recommendations */}
      {heatmapData.insights.recommendations.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold mb-4">💡 Key Recommendations</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {heatmapData.insights.recommendations.map((rec, index) => (
              <div 
                key={index} 
                className={`p-4 rounded-lg border-l-4 ${
                  rec.priority === 'high' 
                    ? 'bg-red-50 border-red-400' 
                    : rec.priority === 'medium'
                    ? 'bg-yellow-50 border-yellow-400'
                    : 'bg-blue-50 border-blue-400'
                }`}
              >
                <div className="flex items-center mb-2">
                  <div className={`text-sm font-medium px-2 py-1 rounded ${
                    rec.priority === 'high' 
                      ? 'bg-red-100 text-red-800' 
                      : rec.priority === 'medium'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}>
                    {rec.priority.toUpperCase()}
                  </div>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">{rec.title}</h4>
                <p className="text-sm text-gray-700 mb-2">{rec.description}</p>
                <p className="text-xs text-gray-600 italic">{rec.expected_impact}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformanceHeatmap;
