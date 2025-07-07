
import React, { useState, useEffect } from 'react';
import { marketDataService } from '../../services/marketData';

interface MarketRegimeIndicatorProps {
  symbols: string[];
}

export const MarketRegimeIndicator: React.FC<MarketRegimeIndicatorProps> = ({ symbols }) => {
  const [regimes, setRegimes] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRegimes = async () => {
      try {
        setLoading(true);
        const regimeData: Record<string, string> = {};
        
        await Promise.all(
          symbols.map(async (symbol) => {
            const result = await marketDataService.getMarketRegime(symbol);
            regimeData[symbol] = result.regime;
          })
        );
        
        setRegimes(regimeData);
      } catch (error) {
        console.error('Failed to fetch market regimes:', error);
      } finally {
        setLoading(false);
      }
    };

    if (symbols.length > 0) {
      fetchRegimes();
      const interval = setInterval(fetchRegimes, 30000); // Update every 30 seconds
      return () => clearInterval(interval);
    }
  }, [symbols]);

  const getRegimeColor = (regime: string) => {
    switch (regime) {
      case 'high_volatility': return 'bg-red-500';
      case 'low_volatility': return 'bg-green-500';
      case 'normal': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getRegimeLabel = (regime: string) => {
    switch (regime) {
      case 'high_volatility': return 'High Vol';
      case 'low_volatility': return 'Low Vol';
      case 'normal': return 'Normal';
      default: return 'Unknown';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">Market Regime</h3>
        <div className="animate-pulse space-y-2">
          {symbols.map(symbol => (
            <div key={symbol} className="h-8 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold mb-4">Market Regime Analysis</h3>
      
      <div className="space-y-3">
        {symbols.map(symbol => {
          const regime = regimes[symbol] || 'unknown';
          return (
            <div key={symbol} className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                <span className="font-medium text-gray-900">{symbol}</span>
                <span className={`w-3 h-3 rounded-full ${getRegimeColor(regime)}`}></span>
              </div>
              <span className="text-sm font-medium text-gray-700">
                {getRegimeLabel(regime)}
              </span>
            </div>
          );
        })}
      </div>
      
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Legend</h4>
        <div className="flex flex-wrap gap-4 text-xs">
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-500"></span>
            <span>High Volatility</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-500"></span>
            <span>Normal</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500"></span>
            <span>Low Volatility</span>
          </div>
        </div>
      </div>
    </div>
  );
};
