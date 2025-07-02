
import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

interface MarketCondition {
  volatility: string;
  trend: string;
  volume: string;
  session: string;
}

interface ConditionAnalytics {
  trades: number;
  wins: number;
  total_pnl: number;
  win_rate: number;
  avg_pnl: number;
  conditions: MarketCondition;
}

interface MarketContextInsightsProps {
  userId?: number;
}

export const MarketContextInsights: React.FC<MarketContextInsightsProps> = ({ userId }) => {
  const [analytics, setAnalytics] = useState<Record<string, ConditionAnalytics>>({});
  const [isEnriching, setIsEnriching] = useState(false);
  const [loading, setLoading] = useState(true);
  const [enrichedCount, setEnrichedCount] = useState(0);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('/api/v1/market-data/analytics/by-conditions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data.analytics || {});
      }
    } catch (error) {
      console.error('Failed to fetch market context analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const enrichTrades = async () => {
    setIsEnriching(true);
    try {
      const response = await fetch('/api/v1/market-data/enrich-trades', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setEnrichedCount(data.enriched_trades);
        await fetchAnalytics(); // Refresh analytics
      }
    } catch (error) {
      console.error('Failed to enrich trades:', error);
    } finally {
      setIsEnriching(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const getConditionColor = (conditionType: string, value: string) => {
    const colors = {
      volatility: {
        high: 'text-red-600',
        medium: 'text-yellow-600',
        low: 'text-green-600'
      },
      trend: {
        strong_bullish: 'text-green-700',
        bullish: 'text-green-500',
        sideways: 'text-gray-500',
        bearish: 'text-red-500',
        strong_bearish: 'text-red-700'
      },
      volume: {
        high: 'text-blue-600',
        normal: 'text-gray-600',
        low: 'text-gray-400'
      }
    };
    
    return colors[conditionType as keyof typeof colors]?.[value as keyof any] || 'text-gray-500';
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Market Context Insights</h3>
          <Button
            onClick={enrichTrades}
            disabled={isEnriching}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isEnriching ? 'Enriching...' : 'Enrich Trades with Market Data'}
          </Button>
        </div>
        
        {enrichedCount > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
            <p className="text-green-800">
              ✅ Successfully enriched {enrichedCount} trades with market context data
            </p>
          </div>
        )}
        
        {Object.keys(analytics).length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No market context data available.</p>
            <p className="text-sm mt-2">Click "Enrich Trades" to add market context to your trades.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(analytics).map(([key, data]) => (
              <Card key={key} className="p-4">
                <div className="space-y-3">
                  <div className="border-b pb-2">
                    <h4 className="font-medium text-gray-900">Market Conditions</h4>
                    <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
                      <div>
                        <span className="text-gray-500">Volatility:</span>
                        <span className={`ml-1 font-medium ${getConditionColor('volatility', data.conditions.volatility)}`}>
                          {data.conditions.volatility}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Trend:</span>
                        <span className={`ml-1 font-medium ${getConditionColor('trend', data.conditions.trend)}`}>
                          {data.conditions.trend.replace('_', ' ')}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Volume:</span>
                        <span className={`ml-1 font-medium ${getConditionColor('volume', data.conditions.volume)}`}>
                          {data.conditions.volume}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Session:</span>
                        <span className="ml-1 font-medium text-gray-700">
                          {data.conditions.session.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Trades:</span>
                      <span className="font-medium">{data.trades}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Win Rate:</span>
                      <span className={`font-medium ${data.win_rate >= 50 ? 'text-green-600' : 'text-red-600'}`}>
                        {data.win_rate.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Avg P&L:</span>
                      <span className={`font-medium ${data.avg_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${data.avg_pnl.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total P&L:</span>
                      <span className={`font-medium ${data.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${data.total_pnl.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

export default MarketContextInsights;
