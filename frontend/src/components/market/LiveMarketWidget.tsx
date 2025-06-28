
import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../ui/Card';
import { marketDataService } from '../../services/marketData';

interface MarketData {
  symbol: string;
  price: number;
  change_percent?: number;
  volume?: number;
  timestamp: string;
  market_open: boolean;
}

interface LiveMarketWidgetProps {
  symbols: string[];
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const LiveMarketWidget: React.FC<LiveMarketWidgetProps> = ({
  symbols,
  autoRefresh = true,
  refreshInterval = 30000
}) => {
  const [marketData, setMarketData] = useState<Record<string, MarketData>>({});
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchMarketData = useCallback(async () => {
    setLoading(true);
    try {
      const promises = symbols.map(symbol => 
        marketDataService.getCurrentPrice(symbol)
      );
      
      const results = await Promise.all(promises);
      const newData: Record<string, MarketData> = {};
      
      results.forEach((data, index) => {
        if (data) {
          newData[symbols[index]] = data;
        }
      });
      
      setMarketData(prev => ({ ...prev, ...newData }));
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching market data:', error);
    } finally {
      setLoading(false);
    }
  }, [symbols]);

  const subscribeToRealTime = useCallback(() => {
    const ws = new WebSocket(`ws://localhost:5000/api/v1/market-data/ws/user123`);
    
    ws.onopen = () => {
      setConnected(true);
      console.log('Connected to real-time market data');
      
      // Subscribe to all symbols
      symbols.forEach(symbol => {
        ws.send(JSON.stringify({
          action: 'subscribe',
          symbol: symbol
        }));
      });
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'market_update') {
        setMarketData(prev => ({
          ...prev,
          [data.symbol]: {
            symbol: data.symbol,
            price: data.price,
            change_percent: data.change_percent,
            volume: data.volume,
            timestamp: data.timestamp,
            market_open: true
          }
        }));
        setLastUpdate(new Date());
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('Disconnected from real-time market data');
      // Fallback to polling
      if (autoRefresh) {
        setTimeout(() => subscribeToRealTime(), 5000);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [symbols, autoRefresh]);

  useEffect(() => {
    // Initial fetch
    fetchMarketData();

    // Try WebSocket first, fallback to polling
    const cleanup = subscribeToRealTime();

    // Polling fallback
    let interval: NodeJS.Timeout;
    if (autoRefresh && !connected) {
      interval = setInterval(fetchMarketData, refreshInterval);
    }

    return () => {
      cleanup && cleanup();
      interval && clearInterval(interval);
    };
  }, [fetchMarketData, subscribeToRealTime, autoRefresh, refreshInterval, connected]);

  const formatPrice = (price: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price);
  };

  const formatChangePercent = (change: number): string => {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  const getChangeColor = (change?: number): string => {
    if (!change) return 'text-gray-500';
    return change >= 0 ? 'text-green-600' : 'text-red-600';
  };

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Live Market Data</h3>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-500">
            {connected ? 'Live' : 'Delayed'}
          </span>
          {lastUpdate && (
            <span className="text-xs text-gray-400">
              {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {symbols.map(symbol => {
          const data = marketData[symbol];
          if (!data) {
            return (
              <div key={symbol} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span className="font-medium">{symbol}</span>
                <div className="animate-pulse bg-gray-300 h-4 w-20 rounded"></div>
              </div>
            );
          }

          return (
            <div key={symbol} className="flex items-center justify-between p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors">
              <div>
                <span className="font-medium">{data.symbol}</span>
                {data.volume && (
                  <div className="text-xs text-gray-500">
                    Vol: {(data.volume / 1000000).toFixed(1)}M
                  </div>
                )}
              </div>
              
              <div className="text-right">
                <div className="font-semibold">
                  {formatPrice(data.price)}
                </div>
                {data.change_percent !== undefined && (
                  <div className={`text-sm ${getChangeColor(data.change_percent)}`}>
                    {formatChangePercent(data.change_percent)}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {loading && (
        <div className="mt-3 text-center">
          <div className="inline-flex items-center text-sm text-gray-500">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
            Updating...
          </div>
        </div>
      )}
    </Card>
  );
};
