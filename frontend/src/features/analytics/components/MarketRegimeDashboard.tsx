
import React, { useState, useEffect } from 'react';
import { Card } from '../../../components/ui/Card';
import { marketDataService, MarketRegime } from '../../../services/marketData';

interface RegimeIndicatorProps {
  regime: MarketRegime;
}

const RegimeIndicator: React.FC<RegimeIndicatorProps> = ({ regime }) => {
  const getRegimeColor = (regimeName: string) => {
    switch (regimeName) {
      case 'bull_trending': return 'text-green-600 bg-green-100';
      case 'bear_trending': return 'text-red-600 bg-red-100';
      case 'high_volatility': return 'text-orange-600 bg-orange-100';
      case 'low_volatility': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRegimeDisplay = (regimeName: string) => {
    return regimeName.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <div className="flex items-center space-x-3">
      <div className={`px-3 py-1 rounded-full text-sm font-medium ${getRegimeColor(regime.regime)}`}>
        {getRegimeDisplay(regime.regime)}
      </div>
      <div className="text-sm text-gray-600">
        Confidence: {(regime.confidence * 100).toFixed(1)}%
      </div>
    </div>
  );
};

const MarketRegimeDashboard: React.FC = () => {
  const [regime, setRegime] = useState<MarketRegime | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMarketRegime();
    
    // Refresh regime analysis every 5 minutes
    const interval = setInterval(loadMarketRegime, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);

  const loadMarketRegime = async () => {
    try {
      setLoading(true);
      const regimeData = await marketDataService.getMarketRegime();
      setRegime(regimeData);
      setError(null);
    } catch (err) {
      setError('Failed to load market regime analysis');
      console.error('Error loading market regime:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-6"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
      </Card>
    );
  }

  if (error || !regime) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="text-red-600 mb-2">⚠️ {error}</div>
          <button
            onClick={loadMarketRegime}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Current Regime Status */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Current Market Regime</h3>
        <RegimeIndicator regime={regime} />
        
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-700">{regime.duration_days}</div>
            <div className="text-sm text-gray-500">Days Active</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${
              regime.risk_level === 'High' ? 'text-red-600' :
              regime.risk_level === 'Medium' ? 'text-yellow-600' : 'text-green-600'
            }`}>
              {regime.risk_level}
            </div>
            <div className="text-sm text-gray-500">Risk Level</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {(regime.confidence * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-gray-500">Confidence</div>
          </div>
        </div>
      </Card>

      {/* Key Indicators */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Key Market Indicators</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(regime.key_indicators).map(([key, value]) => (
            <div key={key} className="bg-gray-50 p-3 rounded">
              <div className="text-sm text-gray-600 capitalize">
                {key.replace(/_/g, ' ')}
              </div>
              <div className="text-lg font-semibold">
                {typeof value === 'number' ? value.toFixed(2) : value}
                {key.includes('percentage') || key.includes('vs') ? '%' : ''}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Strategy Recommendations */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Recommended Strategies</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {regime.recommended_strategies.map((strategy, index) => (
            <div
              key={index}
              className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg"
            >
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
              <span className="text-sm font-medium text-blue-800">{strategy}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Refresh Info */}
      <div className="text-center text-sm text-gray-500">
        Last updated: {new Date().toLocaleTimeString()} • Auto-refresh every 5 minutes
      </div>
    </div>
  );
};

export default MarketRegimeDashboard;
