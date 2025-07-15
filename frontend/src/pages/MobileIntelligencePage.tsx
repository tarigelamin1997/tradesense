
import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { LiveMarketWidget } from '../components/market/LiveMarketWidget';
import { MarketSentimentIndicator } from '../components/market/MarketSentimentIndicator';

interface TradeSignal {
  id: string;
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  reason: string;
  timestamp: string;
}

interface MarketAlert {
  id: string;
  type: 'VOLATILITY' | 'MOMENTUM' | 'SUPPORT' | 'RESISTANCE';
  message: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  timestamp: string;
}

export const MobileIntelligencePage: React.FC = () => {
  const [signals, setSignals] = useState<TradeSignal[]>([]);
  const [alerts, setAlerts] = useState<MarketAlert[]>([]);
  const [selectedTab, setSelectedTab] = useState<'signals' | 'alerts' | 'watchlist'>('signals');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchIntelligenceData();
    
    // Set up real-time updates
    const interval = setInterval(fetchIntelligenceData, 30000); // Every 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  const fetchIntelligenceData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Fetch trade signals
      const signalsResponse = await fetch('/api/v1/intelligence/signals', { headers });
      const signalsData = await signalsResponse.json();
      setSignals(signalsData.data?.signals || []);

      // Fetch market alerts
      const alertsResponse = await fetch('/api/v1/intelligence/alerts', { headers });
      const alertsData = await alertsResponse.json();
      setAlerts(alertsData.data?.alerts || []);

      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch intelligence data:', error);
      setIsLoading(false);
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'BUY': return 'text-green-600 bg-green-100';
      case 'SELL': return 'text-red-600 bg-red-100';
      default: return 'text-yellow-600 bg-yellow-100';
    }
  };

  const getAlertSeverityColor = (severity: string) => {
    switch (severity) {
      case 'HIGH': return 'border-l-red-500 bg-red-50';
      case 'MEDIUM': return 'border-l-yellow-500 bg-yellow-50';
      default: return 'border-l-blue-500 bg-blue-50';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading intelligence data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="px-4 py-3">
          <h1 className="text-xl font-bold text-gray-900">Trade Intelligence</h1>
          <p className="text-sm text-gray-600">Real-time market insights</p>
        </div>
      </div>

      {/* Live Market Overview */}
      <div className="p-4 space-y-4">
        <Card className="p-4">
          <h2 className="text-lg font-semibold mb-3">Market Overview</h2>
          <div className="grid grid-cols-2 gap-4">
            <LiveMarketWidget />
            <MarketSentimentIndicator />
          </div>
        </Card>

        {/* Tab Navigation */}
        <div className="flex bg-white rounded-lg p-1 shadow-sm">
          <button
            onClick={() => setSelectedTab('signals')}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
              selectedTab === 'signals'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Signals ({signals.length})
          </button>
          <button
            onClick={() => setSelectedTab('alerts')}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
              selectedTab === 'alerts'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Alerts ({alerts.length})
          </button>
          <button
            onClick={() => setSelectedTab('watchlist')}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
              selectedTab === 'watchlist'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Watchlist
          </button>
        </div>

        {/* Content based on selected tab */}
        {selectedTab === 'signals' && (
          <div className="space-y-3">
            {signals.length === 0 ? (
              <Card className="p-6 text-center">
                <div className="text-gray-500">
                  <div className="text-4xl mb-2">📊</div>
                  <p>No active signals</p>
                  <p className="text-sm">Check back soon for new opportunities</p>
                </div>
              </Card>
            ) : (
              signals.map((signal) => (
                <Card key={signal.id} className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <span className="font-bold text-lg">{signal.symbol}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSignalColor(signal.signal)}`}>
                        {signal.signal}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">{signal.confidence}% confidence</div>
                      <div className="text-xs text-gray-500">
                        {new Date(signal.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-gray-700">{signal.reason}</p>
                  <div className="mt-3 flex space-x-2">
                    <Button size="sm" variant="primary" className="flex-1">
                      View Details
                    </Button>
                    <Button size="sm" variant="outline" className="flex-1">
                      Add to Watchlist
                    </Button>
                  </div>
                </Card>
              ))
            )}
          </div>
        )}

        {selectedTab === 'alerts' && (
          <div className="space-y-3">
            {alerts.length === 0 ? (
              <Card className="p-6 text-center">
                <div className="text-gray-500">
                  <div className="text-4xl mb-2">🔔</div>
                  <p>No active alerts</p>
                  <p className="text-sm">Market conditions are stable</p>
                </div>
              </Card>
            ) : (
              alerts.map((alert) => (
                <Card key={alert.id} className={`p-4 border-l-4 ${getAlertSeverityColor(alert.severity)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm text-gray-800">{alert.type}</span>
                    <span className="text-xs text-gray-500">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700">{alert.message}</p>
                </Card>
              ))
            )}
          </div>
        )}

        {selectedTab === 'watchlist' && (
          <Card className="p-6 text-center">
            <div className="text-gray-500">
              <div className="text-4xl mb-2">⭐</div>
              <p>Watchlist feature</p>
              <p className="text-sm">Coming soon...</p>
            </div>
          </Card>
        )}
      </div>

      {/* Floating Action Button */}
      <div className="fixed bottom-6 right-6">
        <Button 
          size="lg" 
          className="rounded-full h-14 w-14 shadow-lg"
          onClick={() => window.location.href = '/trades/add'}
        >
          <span className="text-xl">+</span>
        </Button>
      </div>
    </div>
  );
};

export default MobileIntelligencePage;
