import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { marketDataService } from '../../services/marketData';

interface MarketQuote {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: string;
  source: string;
}

interface MarketSentiment {
  symbol: string;
  sentiment_score: number;
  sentiment_label: string;
  volatility: number;
  rsi: number;
  ma_signal: string;
}

interface LiveMarketWidgetProps {
  symbols?: string[];
  showSentiment?: boolean;
  refreshInterval?: number;
}

export const LiveMarketWidget: React.FC<LiveMarketWidgetProps> = ({
  symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA'],
  showSentiment = true,
  refreshInterval = 30000 // 30 seconds
}) => {
  const [quotes, setQuotes] = useState<MarketQuote[]>([]);
  const [sentiments, setSentiments] = useState<Record<string, MarketSentiment>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchMarketData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch quotes
      const quotesResponse = await marketDataService.getBatchQuotes(symbols.join(','));
      setQuotes(quotesResponse.quotes);

      // Fetch sentiment data if enabled
      if (showSentiment) {
        const sentimentPromises = symbols.map(async (symbol) => {
          try {
            const sentiment = await marketDataService.getMarketSentiment(symbol);
            return { symbol, sentiment };
          } catch (error) {
            console.warn(`Failed to fetch sentiment for ${symbol}:`, error);
            return null;
          }
        });

        const sentimentResults = await Promise.all(sentimentPromises);
        const sentimentMap: Record<string, MarketSentiment> = {};

        sentimentResults.forEach((result) => {
          if (result) {
            sentimentMap[result.symbol] = result.sentiment;
          }
        });

        setSentiments(sentimentMap);
      }

      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch market data:', error);
      setError('Failed to load market data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMarketData();

    const interval = setInterval(fetchMarketData, refreshInterval);
    return () => clearInterval(interval);
  }, [symbols, showSentiment, refreshInterval]);

  const formatPrice = (price: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price);
  };

  const formatPercent = (percent: number): string => {
    return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
  };

  const getChangeColor = (change: number): string => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getSentimentColor = (score: number): string => {
    if (score > 0.2) return 'text-green-600';
    if (score < -0.2) return 'text-red-600';
    return 'text-yellow-600';
  };

  const getSentimentIcon = (score: number): string => {
    if (score > 0.2) return '📈';
    if (score < -0.2) return '📉';
    return '➡️';
  };

  if (loading && quotes.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Live Market Data</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2">Loading market data...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Live Market Data</CardTitle>
        <div className="flex items-center space-x-2">
          {lastUpdate && (
            <span className="text-sm text-gray-500">
              Last update: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <Button 
            onClick={fetchMarketData} 
            disabled={loading}
            size="sm"
            variant="outline"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            ) : (
              '🔄'
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        <div className="space-y-3">
          {quotes.map((quote) => {
            const sentiment = sentiments[quote.symbol];

            return (
              <div
                key={quote.symbol}
                className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="font-semibold text-lg">{quote.symbol}</div>
                    <div className="text-2xl font-bold">
                      {formatPrice(quote.price)}
                    </div>
                    <div className={`font-medium ${getChangeColor(quote.change)}`}>
                      {formatPrice(quote.change)} ({formatPercent(quote.change_percent)})
                    </div>
                  </div>

                  {showSentiment && sentiment && (
                    <div className="text-right">
                      <div className={`flex items-center space-x-1 ${getSentimentColor(sentiment.sentiment_score)}`}>
                        <span>{getSentimentIcon(sentiment.sentiment_score)}</span>
                        <span className="font-medium">{sentiment.sentiment_label}</span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        RSI: {sentiment.rsi.toFixed(1)} | Vol: {sentiment.volatility.toFixed(2)}%
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between mt-2 text-sm text-gray-500">
                  <div>Volume: {quote.volume.toLocaleString()}</div>
                  <div>Source: {quote.source}</div>
                </div>

                {showSentiment && sentiment && (
                  <div className="mt-2 flex items-center space-x-4 text-xs">
                    <div className={`px-2 py-1 rounded-full ${
                      sentiment.ma_signal === 'bullish' ? 'bg-green-100 text-green-800' :
                      sentiment.ma_signal === 'bearish' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      MA: {sentiment.ma_signal}
                    </div>
                    <div className="text-gray-600">
                      Sentiment: {(sentiment.sentiment_score * 100).toFixed(0)}/100
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {quotes.length === 0 && !loading && (
          <div className="text-center py-8 text-gray-500">
            No market data available
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default LiveMarketWidget;