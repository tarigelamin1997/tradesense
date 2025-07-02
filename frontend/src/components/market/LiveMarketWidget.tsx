
import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../ui/Card';

interface MarketData {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  bid?: number;
  ask?: number;
  high?: number;
  low?: number;
  timestamp: string;
  sentiment?: {
    score: number;
    volatility: number;
    momentum: number;
    trend: string;
  };
}

interface LiveMarketWidgetProps {
  symbols: string[];
  onSymbolClick?: (symbol: string) => void;
  showSentiment?: boolean;
  compact?: boolean;
}

export const LiveMarketWidget: React.FC<LiveMarketWidgetProps> = ({
  symbols,
  onSymbolClick,
  showSentiment = true,
  compact = false
}) => {
  const [marketData, setMarketData] = useState<Record<string, MarketData>>({});
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [ws, setWs] = useState<WebSocket | null>(null);

  const connectWebSocket = useCallback(() => {
    const token = localStorage.getItem('auth_token');
    const userId = localStorage.getItem('user_id');
    
    if (!token || !userId) return;

    const wsUrl = `ws://localhost:5000/api/v1/market-data/ws/${userId}`;
    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
      setConnectionStatus('connected');
      console.log('Market data WebSocket connected');
      
      // Subscribe to symbols
      symbols.forEach(symbol => {
        websocket.send(JSON.stringify({
          type: 'subscribe',
          symbol: symbol
        }));
      });
    };

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        if (message.type === 'market_update') {
          const data = message.data;
          setMarketData(prev => ({
            ...prev,
            [data.symbol]: data
          }));
        }
      } catch (error) {
        console.error('Error parsing market data:', error);
      }
    };

    websocket.onclose = () => {
      setConnectionStatus('disconnected');
      console.log('Market data WebSocket disconnected');
      
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        if (symbols.length > 0) {
          connectWebSocket();
        }
      }, 5000);
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('disconnected');
    };

    setWs(websocket);
  }, [symbols]);

  useEffect(() => {
    if (symbols.length > 0) {
      connectWebSocket();
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [symbols, connectWebSocket]);

  const formatPrice = (price: number) => {
    return price.toFixed(2);
  };

  const formatChange = (change: number, changePercent: number) => {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)} (${sign}${changePercent.toFixed(2)}%)`;
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getSentimentColor = (score: number) => {
    if (score > 0.3) return 'text-green-600';
    if (score < -0.3) return 'text-red-600';
    return 'text-yellow-600';
  };

  const getSentimentLabel = (score: number) => {
    if (score > 0.5) return 'Very Bullish';
    if (score > 0.2) return 'Bullish';
    if (score > -0.2) return 'Neutral';
    if (score > -0.5) return 'Bearish';
    return 'Very Bearish';
  };

  if (compact) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">Live Market Data</span>
          <div className={`flex items-center ${
            connectionStatus === 'connected' ? 'text-green-600' : 
            connectionStatus === 'connecting' ? 'text-yellow-600' : 'text-red-600'
          }`}>
            <div className={`w-2 h-2 rounded-full mr-2 ${
              connectionStatus === 'connected' ? 'bg-green-600' : 
              connectionStatus === 'connecting' ? 'bg-yellow-600' : 'bg-red-600'
            }`} />
            {connectionStatus}
          </div>
        </div>

        {symbols.map(symbol => {
          const data = marketData[symbol];
          if (!data) {
            return (
              <div key={symbol} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span className="font-medium">{symbol}</span>
                <span className="text-gray-500">Loading...</span>
              </div>
            );
          }

          return (
            <div 
              key={symbol} 
              className="flex items-center justify-between p-2 bg-white border rounded cursor-pointer hover:bg-gray-50"
              onClick={() => onSymbolClick?.(symbol)}
            >
              <div>
                <div className="font-medium">{symbol}</div>
                <div className={`text-sm ${getChangeColor(data.change)}`}>
                  {formatChange(data.change, data.change_percent)}
                </div>
              </div>
              <div className="text-right">
                <div className="font-bold">${formatPrice(data.price)}</div>
                {showSentiment && data.sentiment && (
                  <div className={`text-xs ${getSentimentColor(data.sentiment.score)}`}>
                    {getSentimentLabel(data.sentiment.score)}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Live Market Data</h3>
        <div className={`flex items-center text-sm ${
          connectionStatus === 'connected' ? 'text-green-600' : 
          connectionStatus === 'connecting' ? 'text-yellow-600' : 'text-red-600'
        }`}>
          <div className={`w-3 h-3 rounded-full mr-2 ${
            connectionStatus === 'connected' ? 'bg-green-600' : 
            connectionStatus === 'connecting' ? 'bg-yellow-600' : 'bg-red-600'
          }`} />
          {connectionStatus}
        </div>
      </div>

      <div className="space-y-4">
        {symbols.map(symbol => {
          const data = marketData[symbol];
          
          if (!data) {
            return (
              <div key={symbol} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-lg">{symbol}</span>
                  <span className="text-gray-500">Loading...</span>
                </div>
              </div>
            );
          }

          return (
            <div 
              key={symbol} 
              className="p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              onClick={() => onSymbolClick?.(symbol)}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-lg">{symbol}</span>
                <span className="text-2xl font-bold">${formatPrice(data.price)}</span>
              </div>
              
              <div className="flex items-center justify-between mb-2">
                <span className={`font-medium ${getChangeColor(data.change)}`}>
                  {formatChange(data.change, data.change_percent)}
                </span>
                <span className="text-sm text-gray-600">
                  Vol: {(data.volume / 1000000).toFixed(1)}M
                </span>
              </div>

              {data.bid && data.ask && (
                <div className="flex items-center justify-between mb-2 text-sm">
                  <span>Bid: ${formatPrice(data.bid)}</span>
                  <span>Ask: ${formatPrice(data.ask)}</span>
                </div>
              )}

              {data.high && data.low && (
                <div className="flex items-center justify-between mb-2 text-sm">
                  <span>High: ${formatPrice(data.high)}</span>
                  <span>Low: ${formatPrice(data.low)}</span>
                </div>
              )}

              {showSentiment && data.sentiment && (
                <div className="mt-3 p-3 bg-gray-50 rounded">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">Market Sentiment</span>
                    <span className={`font-bold ${getSentimentColor(data.sentiment.score)}`}>
                      {getSentimentLabel(data.sentiment.score)}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <span className="text-gray-600">Volatility:</span>
                      <div className="font-medium">{data.sentiment.volatility.toFixed(1)}%</div>
                    </div>
                    <div>
                      <span className="text-gray-600">Momentum:</span>
                      <div className={`font-medium ${getChangeColor(data.sentiment.momentum)}`}>
                        {data.sentiment.momentum.toFixed(1)}
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">Trend:</span>
                      <div className="font-medium capitalize">{data.sentiment.trend}</div>
                    </div>
                  </div>
                </div>
              )}

              <div className="mt-2 text-xs text-gray-500">
                Last updated: {new Date(data.timestamp).toLocaleTimeString()}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

export default LiveMarketWidget;
