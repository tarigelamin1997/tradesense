
import React, { useState } from 'react';
import { LiveMarketWidget } from '../components/market/LiveMarketWidget';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

const LiveMarketPage: React.FC = () => {
  const [watchlistSymbols, setWatchlistSymbols] = useState<string[]>([
    'AAPL', 'TSLA', 'NVDA', 'SPY', 'QQQ'
  ]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('AAPL');
  const [newSymbol, setNewSymbol] = useState<string>('');

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
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Live Market Data
          </h1>
          <p className="text-gray-600">
            Real-time market data and sentiment analysis for your watchlist
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Watchlist Management */}
          <div className="lg:col-span-1">
            <Card className="p-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">Manage Watchlist</h3>
              
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                  placeholder="Add symbol..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onKeyPress={(e) => e.key === 'Enter' && addSymbol()}
                />
                <Button onClick={addSymbol}>Add</Button>
              </div>

              <div className="space-y-2">
                {watchlistSymbols.map(symbol => (
                  <div key={symbol} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span 
                      className="font-medium cursor-pointer hover:text-blue-600"
                      onClick={() => setSelectedSymbol(symbol)}
                    >
                      {symbol}
                    </span>
                    <button
                      onClick={() => removeSymbol(symbol)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            </Card>

            {/* Compact Watchlist */}
            <LiveMarketWidget 
              symbols={watchlistSymbols}
              onSymbolClick={setSelectedSymbol}
              compact={true}
            />
          </div>

          {/* Detailed View */}
          <div className="lg:col-span-2">
            <LiveMarketWidget 
              symbols={[selectedSymbol]}
              showSentiment={true}
              compact={false}
            />

            {/* Market Status */}
            <Card className="p-6 mt-6">
              <h3 className="text-lg font-semibold mb-4">Market Status</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">OPEN</div>
                  <div className="text-sm text-gray-600">US Markets</div>
                </div>
                
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">4:00 PM</div>
                  <div className="text-sm text-gray-600">Market Close</div>
                </div>
                
                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">DEMO</div>
                  <div className="text-sm text-gray-600">Data Mode</div>
                </div>
              </div>
            </Card>

            {/* Trading Insights */}
            <Card className="p-6 mt-6">
              <h3 className="text-lg font-semibold mb-4">Market Insights</h3>
              
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
                  <div className="font-medium text-blue-800">Market Regime: Bullish Trending</div>
                  <div className="text-sm text-blue-600 mt-1">
                    Strong momentum and positive sentiment across major indices
                  </div>
                </div>
                
                <div className="p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded">
                  <div className="font-medium text-yellow-800">Volatility Alert</div>
                  <div className="text-sm text-yellow-600 mt-1">
                    Increased volatility detected in tech sector - manage risk carefully
                  </div>
                </div>
                
                <div className="p-4 bg-green-50 border-l-4 border-green-500 rounded">
                  <div className="font-medium text-green-800">Sector Strength</div>
                  <div className="text-sm text-green-600 mt-1">
                    Technology and Growth stocks showing strong relative performance
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMarketPage;
