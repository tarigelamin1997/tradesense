
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
