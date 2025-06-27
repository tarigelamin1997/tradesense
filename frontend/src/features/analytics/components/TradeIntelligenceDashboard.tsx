
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { Alert, AlertDescription } from '../../../components/ui/Alert';

interface TradeAnalysis {
  overall_score: number;
  risk_level: string;
  score_components: Record<string, number>;
  recommendations: string[];
  confidence_interval: [number, number];
  expected_outcome: {
    win_probability: number;
    expected_return_pct: number;
    risk_reward_ratio: number;
  };
}

interface MarketRegime {
  regime_type: string;
  confidence_score: number;
  volatility_level: string;
  recommendations: string[];
}

const TradeIntelligenceDashboard: React.FC = () => {
  const [tradeData, setTradeData] = useState({
    symbol: '',
    side: 'long',
    quantity: '',
    strategy: '',
    entry_price: '',
    stop_loss: '',
    take_profit: ''
  });
  
  const [analysis, setAnalysis] = useState<TradeAnalysis | null>(null);
  const [marketRegime, setMarketRegime] = useState<MarketRegime | null>(null);
  const [loading, setLoading] = useState(false);
  const [insights, setInsights] = useState<any>(null);

  useEffect(() => {
    fetchMarketRegime();
    fetchTradingInsights();
  }, []);

  const fetchMarketRegime = async () => {
    try {
      const response = await fetch('/api/v1/intelligence/market-regime', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setMarketRegime(data);
    } catch (error) {
      console.error('Error fetching market regime:', error);
    }
  };

  const fetchTradingInsights = async () => {
    try {
      const response = await fetch('/api/v1/intelligence/trading-insights', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setInsights(data);
    } catch (error) {
      console.error('Error fetching insights:', error);
    }
  };

  const analyzeTrade = async () => {
    if (!tradeData.symbol || !tradeData.quantity || !tradeData.strategy) {
      alert('Please fill in symbol, quantity, and strategy');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/intelligence/analyze-trade', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          ...tradeData,
          quantity: parseFloat(tradeData.quantity),
          entry_price: tradeData.entry_price ? parseFloat(tradeData.entry_price) : null,
          stop_loss: tradeData.stop_loss ? parseFloat(tradeData.stop_loss) : null,
          take_profit: tradeData.take_profit ? parseFloat(tradeData.take_profit) : null
        })
      });
      
      const result = await response.json();
      setAnalysis(result.analysis);
    } catch (error) {
      console.error('Error analyzing trade:', error);
      alert('Failed to analyze trade');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRiskColor = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Market Regime Card */}
        {marketRegime && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                🌍 Market Regime Analysis
              </CardTitle>
              <CardDescription>
                Current market conditions and recommendations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="font-medium">Regime Type:</span>
                  <span className={`px-2 py-1 rounded text-sm font-medium ${
                    marketRegime.regime_type === 'bull' ? 'bg-green-100 text-green-800' :
                    marketRegime.regime_type === 'bear' ? 'bg-red-100 text-red-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {marketRegime.regime_type.toUpperCase()}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="font-medium">Confidence:</span>
                  <span>{(marketRegime.confidence_score * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="font-medium">Volatility:</span>
                  <span className="capitalize">{marketRegime.volatility_level}</span>
                </div>
                <div className="mt-4">
                  <h4 className="font-medium mb-2">Recommendations:</h4>
                  <ul className="space-y-1 text-sm">
                    {marketRegime.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Trading Insights Card */}
        {insights && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                💡 Personal Trading Insights
              </CardTitle>
              <CardDescription>
                AI-powered recommendations based on your trading history
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {insights.next_steps?.map((step: string, idx: number) => (
                  <Alert key={idx}>
                    <AlertDescription>{step}</AlertDescription>
                  </Alert>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Trade Analysis Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🎯 Pre-Trade Analysis
          </CardTitle>
          <CardDescription>
            Get AI-powered scoring and recommendations before executing your trade
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium mb-1">Symbol *</label>
              <Input
                value={tradeData.symbol}
                onChange={(e) => setTradeData({...tradeData, symbol: e.target.value.toUpperCase()})}
                placeholder="AAPL, TSLA, etc."
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Side</label>
              <select 
                className="w-full p-2 border rounded-md"
                value={tradeData.side}
                onChange={(e) => setTradeData({...tradeData, side: e.target.value})}
              >
                <option value="long">Long</option>
                <option value="short">Short</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Quantity *</label>
              <Input
                type="number"
                value={tradeData.quantity}
                onChange={(e) => setTradeData({...tradeData, quantity: e.target.value})}
                placeholder="100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Strategy *</label>
              <Input
                value={tradeData.strategy}
                onChange={(e) => setTradeData({...tradeData, strategy: e.target.value})}
                placeholder="momentum, breakout, etc."
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Entry Price</label>
              <Input
                type="number"
                step="0.01"
                value={tradeData.entry_price}
                onChange={(e) => setTradeData({...tradeData, entry_price: e.target.value})}
                placeholder="150.00"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Stop Loss</label>
              <Input
                type="number"
                step="0.01"
                value={tradeData.stop_loss}
                onChange={(e) => setTradeData({...tradeData, stop_loss: e.target.value})}
                placeholder="145.00"
              />
            </div>
          </div>
          
          <Button 
            onClick={analyzeTrade}
            disabled={loading}
            className="w-full md:w-auto"
          >
            {loading ? 'Analyzing...' : '🔍 Analyze Trade'}
          </Button>
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {analysis && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>📊 Trade Score</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center mb-4">
                <div className={`text-4xl font-bold ${getScoreColor(analysis.overall_score)}`}>
                  {analysis.overall_score}
                </div>
                <div className="text-sm text-gray-500 mb-2">
                  Confidence: {analysis.confidence_interval[0]}% - {analysis.confidence_interval[1]}%
                </div>
                <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(analysis.risk_level)}`}>
                  {analysis.risk_level} Risk
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium">Score Breakdown:</h4>
                {Object.entries(analysis.score_components).map(([component, score]) => (
                  <div key={component} className="flex justify-between items-center">
                    <span className="text-sm capitalize">{component.replace('_', ' ')}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{width: `${score * 100}%`}}
                        ></div>
                      </div>
                      <span className="text-sm w-8">{Math.round(score * 100)}</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium mb-2">Expected Outcome:</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Win Probability:</span>
                    <div className="font-medium">{analysis.expected_outcome.win_probability}%</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Expected Return:</span>
                    <div className="font-medium">{analysis.expected_outcome.expected_return_pct}%</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>💡 AI Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analysis.recommendations.map((rec, idx) => (
                  <Alert key={idx}>
                    <AlertDescription>{rec}</AlertDescription>
                  </Alert>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default TradeIntelligenceDashboard;
