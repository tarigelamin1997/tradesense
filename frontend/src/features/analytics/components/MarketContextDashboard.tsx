
import React, { useState, useEffect } from 'react';
import { Card } from '../../../components/ui/Card';
import { marketContextService, MarketContext, MarketCondition, SectorPerformance } from '../../../services/marketContext';

interface MarketContextDashboardProps {
  symbol?: string;
  tradeDate?: string;
}

export const MarketContextDashboard: React.FC<MarketContextDashboardProps> = ({ 
  symbol = 'SPY', 
  tradeDate 
}) => {
  const [marketContext, setMarketContext] = useState<MarketContext | null>(null);
  const [conditions, setConditions] = useState<MarketCondition[]>([]);
  const [sectors, setSectors] = useState<SectorPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState(symbol);

  useEffect(() => {
    loadMarketData();
  }, [selectedSymbol, tradeDate]);

  const loadMarketData = async () => {
    try {
      setLoading(true);
      const [contextData, conditionsData, sectorsData] = await Promise.all([
        marketContextService.getMarketContext(selectedSymbol, tradeDate),
        marketContextService.getMarketConditions(),
        marketContextService.getSectorPerformance()
      ]);

      setMarketContext(contextData);
      setConditions(conditionsData);
      setSectors(sectorsData);
    } catch (error) {
      console.error('Error loading market data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getConditionColor = (condition: string) => {
    switch (condition) {
      case 'bullish': return 'text-green-600 bg-green-50';
      case 'bearish': return 'text-red-600 bg-red-50';
      case 'volatile': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getVolatilityLevel = (volatility: number) => {
    if (volatility > 60) return { label: 'High', color: 'text-red-600' };
    if (volatility > 30) return { label: 'Medium', color: 'text-yellow-600' };
    return { label: 'Low', color: 'text-green-600' };
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish': return 'text-green-600';
      case 'bearish': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Market Context Analysis</h2>
        <div className="flex items-center space-x-4">
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="SPY">SPY</option>
            <option value="QQQ">QQQ</option>
            <option value="AAPL">AAPL</option>
            <option value="MSFT">MSFT</option>
            <option value="TSLA">TSLA</option>
          </select>
        </div>
      </div>

      {marketContext && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Market Condition */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Market Condition</h3>
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getConditionColor(marketContext.market_condition)}`}>
              {marketContext.market_condition.toUpperCase()}
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Current market trend and overall direction
            </p>
          </Card>

          {/* Volatility */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Volatility</h3>
            <div className="flex items-center space-x-2">
              <span className="text-2xl font-bold text-gray-900">
                {marketContext.volatility.toFixed(1)}%
              </span>
              <span className={`text-sm font-medium ${getVolatilityLevel(marketContext.volatility).color}`}>
                {getVolatilityLevel(marketContext.volatility).label}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
              <div 
                className="bg-blue-600 h-2 rounded-full" 
                style={{ width: `${Math.min(marketContext.volatility, 100)}%` }}
              ></div>
            </div>
          </Card>

          {/* Volume Profile */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Volume Profile</h3>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold text-gray-900">
                {marketContext.volume_profile.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Trading volume relative to average
            </p>
          </Card>

          {/* Technical Indicators */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Technical Indicators</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">RSI:</span>
                <span className="text-sm font-medium">{marketContext.technical_indicators.rsi}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">MACD:</span>
                <span className={`text-sm font-medium ${getSentimentColor(marketContext.technical_indicators.macd_signal)}`}>
                  {marketContext.technical_indicators.macd_signal}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Trend:</span>
                <span className="text-sm font-medium">
                  {marketContext.technical_indicators.moving_average_trend}
                </span>
              </div>
            </div>
          </Card>

          {/* Market Sentiment */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Market Sentiment</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Fear & Greed:</span>
                <span className="text-sm font-medium">{marketContext.market_sentiment.fear_greed_index}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">VIX Level:</span>
                <span className="text-sm font-medium">{marketContext.market_sentiment.vix_level}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Sentiment:</span>
                <span className={`text-sm font-medium ${getSentimentColor(marketContext.market_sentiment.sentiment_score)}`}>
                  {marketContext.market_sentiment.sentiment_score}
                </span>
              </div>
            </div>
          </Card>

          {/* Sector Performance */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Sector Context</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Sector:</span>
                <span className="text-sm font-medium">{marketContext.sector_performance.sector}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Performance:</span>
                <span className="text-sm font-medium">{marketContext.sector_performance.sector_performance}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Relative Strength:</span>
                <span className="text-sm font-medium">{marketContext.sector_performance.relative_strength}</span>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Economic Events */}
      {marketContext && marketContext.economic_events.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Economic Events</h3>
          <div className="flex flex-wrap gap-2">
            {marketContext.economic_events.map((event, index) => (
              <span key={index} className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
                {event}
              </span>
            ))}
          </div>
        </Card>
      )}

      {/* Sector Performance Table */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Sector Performance</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sector</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Performance</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Change</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sectors.map((sector, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{sector.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{sector.performance}</td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                    sector.change.startsWith('+') ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {sector.change}
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
