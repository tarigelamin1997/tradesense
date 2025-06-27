
import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';

interface LiveQuote {
  symbol: string;
  price: number;
  change: number;
  change_percent: string;
  volume: number;
  market_state: string;
  timestamp: string;
}

interface LiveMarketWidgetProps {
  symbols: string[];
  refreshInterval?: number;
}

export const LiveMarketWidget: React.FC<LiveMarketWidgetProps> = ({ 
  symbols, 
  refreshInterval = 5000 
}) => {
  const [quotes, setQuotes] = useState<LiveQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchQuotes = async () => {
      try {
        const symbolsStr = symbols.join(',');
        const response = await fetch(`/api/v1/market-data/watchlist?symbols=${symbolsStr}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (!response.ok) throw new Error('Failed to fetch quotes');
        
        const data = await response.json();
        setQuotes(data.data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchQuotes();
    const interval = setInterval(fetchQuotes, refreshInterval);

    return () => clearInterval(interval);
  }, [symbols, refreshInterval]);

  const getChangeColor = (change: number): string => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getMarketStateColor = (state: string): string => {
    switch (state) {
      case 'open': return 'bg-green-100 text-green-800';
      case 'closed': return 'bg-red-100 text-red-800';
      case 'after_hours': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <Card className="p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
          <div className="space-y-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-4 border-red-200">
        <div className="text-red-600">
          <h3 className="font-semibold">Market Data Error</h3>
          <p className="text-sm">{error}</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Live Market Data</h3>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-500">Live</span>
        </div>
      </div>

      <div className="space-y-3">
        {quotes.map((quote) => (
          <div 
            key={quote.symbol} 
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center space-x-3">
              <div>
                <div className="font-semibold text-gray-900">{quote.symbol}</div>
                <span className={`text-xs px-2 py-1 rounded-full ${getMarketStateColor(quote.market_state)}`}>
                  {quote.market_state.replace('_', ' ')}
                </span>
              </div>
            </div>

            <div className="text-right">
              <div className="font-semibold text-lg">${quote.price.toFixed(2)}</div>
              <div className={`text-sm ${getChangeColor(quote.change)}`}>
                {quote.change > 0 ? '+' : ''}{quote.change.toFixed(2)} ({quote.change_percent})
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 text-xs text-gray-500 text-center">
        Last updated: {new Date().toLocaleTimeString()}
      </div>
    </Card>
  );
};
import React, { useState, useEffect } from 'react';
import { marketDataService } from '../../services/api';

interface MarketData {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  market_state: string;
  volatility_indicator: string;
  market_trend: string;
}

interface LiveMarketWidgetProps {
  symbol: string;
  className?: string;
}

export const LiveMarketWidget: React.FC<LiveMarketWidgetProps> = ({ 
  symbol, 
  className = '' 
}) => {
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubscribed, setIsSubscribed] = useState(false);

  useEffect(() => {
    const subscribeToSymbol = async () => {
      try {
        setLoading(true);
        setError(null);

        // Subscribe to the symbol
        const subscribeResponse = await marketDataService.subscribeToSymbol(symbol);
        if (subscribeResponse.success) {
          setIsSubscribed(true);
          
          // Wait a moment then fetch initial data
          setTimeout(async () => {
            try {
              const dataResponse = await marketDataService.getMarketData(symbol);
              if (dataResponse.success && dataResponse.data) {
                setMarketData(dataResponse.data);
              }
            } catch (err) {
              console.error('Error fetching initial market data:', err);
            } finally {
              setLoading(false);
            }
          }, 2000);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to subscribe to market data');
        setLoading(false);
      }
    };

    if (symbol) {
      subscribeToSymbol();
    }

    // Set up polling for updates
    const interval = setInterval(async () => {
      if (isSubscribed && symbol) {
        try {
          const response = await marketDataService.getMarketData(symbol);
          if (response.success && response.data) {
            setMarketData(response.data);
          }
        } catch (err) {
          console.error('Error updating market data:', err);
        }
      }
    }, 5000); // Update every 5 seconds

    return () => {
      clearInterval(interval);
      // Cleanup subscription when component unmounts
      if (isSubscribed) {
        marketDataService.unsubscribeFromSymbol(symbol).catch(console.error);
      }
    };
  }, [symbol]);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1000000) {
      return `${(volume / 1000000).toFixed(1)}M`;
    } else if (volume >= 1000) {
      return `${(volume / 1000).toFixed(1)}K`;
    }
    return volume.toString();
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getMarketStateColor = (state: string) => {
    switch (state) {
      case 'REGULAR': return 'text-green-600';
      case 'PRE': return 'text-blue-600';
      case 'POST': return 'text-orange-600';
      case 'CLOSED': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'BULLISH': return '📈';
      case 'BEARISH': return '📉';
      case 'SIDEWAYS': return '➡️';
      default: return '❓';
    }
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-4 ${className}`}>
        <div className="flex items-center justify-center h-24">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading market data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow p-4 ${className}`}>
        <div className="text-center text-red-600">
          <p className="font-medium">Error loading market data</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  if (!marketData) {
    return (
      <div className={`bg-white rounded-lg shadow p-4 ${className}`}>
        <div className="text-center text-gray-600">
          <p>No market data available for {symbol}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900">{symbol}</h3>
        <div className="flex items-center space-x-2">
          <span className={`text-sm font-medium ${getMarketStateColor(marketData.market_state)}`}>
            {marketData.market_state}
          </span>
          {isSubscribed && (
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" title="Live data" />
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-2xl font-bold text-gray-900">
            {formatPrice(marketData.price)}
          </div>
          <div className={`text-sm font-medium ${getChangeColor(marketData.change)}`}>
            {marketData.change > 0 ? '+' : ''}{formatPrice(marketData.change)} 
            ({marketData.change_percent > 0 ? '+' : ''}{marketData.change_percent.toFixed(2)}%)
          </div>
        </div>

        <div className="text-right">
          <div className="text-sm text-gray-600">Volume</div>
          <div className="text-lg font-semibold text-gray-900">
            {formatVolume(marketData.volume)}
          </div>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1">
            <span className="text-gray-600">Trend:</span>
            <span className="font-medium">
              {getTrendIcon(marketData.market_trend)} {marketData.market_trend}
            </span>
          </div>
          
          <div className="flex items-center space-x-1">
            <span className="text-gray-600">Vol:</span>
            <span className={`font-medium ${
              marketData.volatility_indicator === 'HIGH' ? 'text-red-600' :
              marketData.volatility_indicator === 'MEDIUM' ? 'text-yellow-600' :
              'text-green-600'
            }`}>
              {marketData.volatility_indicator}
            </span>
          </div>
        </div>

        <div className="text-xs text-gray-500">
          Live • Updates every 5s
        </div>
      </div>
    </div>
  );
};

export default LiveMarketWidget;
