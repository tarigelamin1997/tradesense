
import React, { useState } from 'react';
import { LiveMarketWidget } from '../components/market/LiveMarketWidget';
import { MarketSentimentIndicator } from '../components/market/MarketSentimentIndicator';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';

export const LiveMarketPage: React.FC = () => {
  const [watchlistSymbols, setWatchlistSymbols] = useState(['AAPL', 'MSFT', 'GOOGL', 'TSLA']);
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [newSymbol, setNewSymbol] = useState('');

  const addSymbol = () => {
    if (newSymbol && !watchlistSymbols.includes(newSymbol.toUpperCase())) {
      setWatchlistSymbols([...watchlistSymbols, newSymbol.toUpperCase()]);
      setNewSymbol('');
    }
  };

  const removeSymbol = (symbol: string) => {
    setWatchlistSymbols(watchlistSymbols.filter(s => s !== symbol));
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Live Market Data</h1>
          <p className="text-gray-600 mt-2">Real-time market information and sentiment analysis</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Watchlist */}
          <div className="lg:col-span-2">
            <LiveMarketWidget symbols={watchlistSymbols} />
            
            {/* Add Symbol */}
            <Card className="p-4 mt-4">
              <h3 className="text-lg font-semibold mb-3">Manage Watchlist</h3>
              <div className="flex space-x-2 mb-3">
                <Input
                  placeholder="Enter symbol (e.g., AAPL)"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                  onKeyPress={(e) => e.key === 'Enter' && addSymbol()}
                />
                <Button onClick={addSymbol}>Add</Button>
              </div>
              
              <div className="flex flex-wrap gap-2">
                {watchlistSymbols.map(symbol => (
                  <div 
                    key={symbol}
                    className="flex items-center bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
                  >
                    <span 
                      className="cursor-pointer"
                      onClick={() => setSelectedSymbol(symbol)}
                    >
                      {symbol}
                    </span>
                    <button
                      onClick={() => removeSymbol(symbol)}
                      className="ml-2 text-blue-600 hover:text-blue-800"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Sentiment Analysis */}
          <div>
            <MarketSentimentIndicator symbol={selectedSymbol} />
            
            <Card className="p-4 mt-4">
              <h3 className="text-lg font-semibold mb-3">Market Alerts</h3>
              <div className="space-y-2">
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                  <div className="font-medium text-yellow-800">Volatility Alert</div>
                  <div className="text-sm text-yellow-700">High volatility detected in tech sector</div>
                </div>
                <div className="p-3 bg-green-50 border border-green-200 rounded">
                  <div className="font-medium text-green-800">Sentiment Shift</div>
                  <div className="text-sm text-green-700">Bullish sentiment increasing for {selectedSymbol}</div>
                </div>
              </div>
            </Card>
          </div>
        </div>

        {/* Market Overview */}
        <Card className="p-6 mt-6">
          <h3 className="text-xl font-semibold mb-4">Market Overview</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">+0.8%</div>
              <div className="text-sm text-gray-600">S&P 500</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">+1.2%</div>
              <div className="text-sm text-gray-600">NASDAQ</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">-0.3%</div>
              <div className="text-sm text-gray-600">DOW</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">45</div>
              <div className="text-sm text-gray-600">Fear & Greed</div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
