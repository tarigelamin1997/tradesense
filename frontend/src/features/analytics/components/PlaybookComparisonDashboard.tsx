
import React, { useState, useEffect } from 'react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { playbookComparisonService } from '../../services/playbookComparison';

interface PlaybookMetrics {
  playbook_name: string;
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  average_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
  total_pnl: number;
  avg_trade_duration: number;
  largest_win: number;
  largest_loss: number;
  consecutive_wins: number;
  consecutive_losses: number;
}

interface ComparisonData {
  metrics: PlaybookMetrics[];
  performance_comparison: {
    playbook_name: string;
    monthly_returns: Array<{
      month: string;
      return: number;
    }>;
  }[];
  risk_analysis: {
    playbook_name: string;
    var_95: number;
    var_99: number;
    expected_shortfall: number;
    volatility: number;
  }[];
}

export const PlaybookComparisonDashboard: React.FC = () => {
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [selectedPlaybooks, setSelectedPlaybooks] = useState<string[]>([]);
  const [availablePlaybooks, setAvailablePlaybooks] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'metrics' | 'performance' | 'risk'>('metrics');

  useEffect(() => {
    loadAvailablePlaybooks();
  }, []);

  const loadAvailablePlaybooks = async () => {
    try {
      const playbooks = await playbookComparisonService.getAvailablePlaybooks();
      setAvailablePlaybooks(playbooks);
      if (playbooks.length >= 2) {
        setSelectedPlaybooks(playbooks.slice(0, 2));
      }
    } catch (error) {
      console.error('Failed to load playbooks:', error);
    }
  };

  const loadComparisonData = async () => {
    if (selectedPlaybooks.length < 2) return;

    setLoading(true);
    try {
      const data = await playbookComparisonService.comparePlaybooks(selectedPlaybooks);
      setComparisonData(data);
    } catch (error) {
      console.error('Failed to load comparison data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedPlaybooks.length >= 2) {
      loadComparisonData();
    }
  }, [selectedPlaybooks]);

  const togglePlaybook = (playbook: string) => {
    setSelectedPlaybooks(prev => {
      if (prev.includes(playbook)) {
        return prev.filter(p => p !== playbook);
      } else {
        return [...prev, playbook];
      }
    });
  };

  const renderMetricsComparison = () => {
    if (!comparisonData?.metrics) return null;

    const metricLabels = [
      { key: 'win_rate', label: 'Win Rate', format: (v: number) => `${(v * 100).toFixed(1)}%` },
      { key: 'profit_factor', label: 'Profit Factor', format: (v: number) => v.toFixed(2) },
      { key: 'average_return', label: 'Avg Return', format: (v: number) => `$${v.toFixed(2)}` },
      { key: 'max_drawdown', label: 'Max Drawdown', format: (v: number) => `${(v * 100).toFixed(1)}%` },
      { key: 'sharpe_ratio', label: 'Sharpe Ratio', format: (v: number) => v.toFixed(2) },
      { key: 'total_pnl', label: 'Total P&L', format: (v: number) => `$${v.toFixed(2)}` }
    ];

    return (
      <div className="space-y-4">
        {metricLabels.map(({ key, label, format }) => (
          <div key={key} className="bg-white p-4 rounded-lg border">
            <h4 className="font-semibold text-gray-700 mb-3">{label}</h4>
            <div className="flex justify-between items-center">
              {comparisonData.metrics.map((playbook, index) => (
                <div key={playbook.playbook_name} className="text-center">
                  <div className="text-sm text-gray-600 mb-1">{playbook.playbook_name}</div>
                  <div className={`text-lg font-bold ${
                    index === 0 ? 'text-blue-600' : 
                    index === 1 ? 'text-green-600' : 'text-purple-600'
                  }`}>
                    {format((playbook as any)[key])}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderPerformanceChart = () => {
    if (!comparisonData?.performance_comparison) return null;

    return (
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4">Monthly Returns Comparison</h3>
        <div className="h-64 flex items-end justify-between space-x-2">
          {comparisonData.performance_comparison[0]?.monthly_returns.map((month, monthIndex) => (
            <div key={month.month} className="flex flex-col items-center space-y-1">
              <div className="flex space-x-1">
                {comparisonData.performance_comparison.map((playbook, playbookIndex) => {
                  const monthData = playbook.monthly_returns[monthIndex];
                  const height = Math.abs(monthData.return) * 2; // Scale for visibility
                  const isPositive = monthData.return >= 0;
                  
                  return (
                    <div
                      key={playbook.playbook_name}
                      className={`w-4 ${
                        playbookIndex === 0 ? 'bg-blue-500' :
                        playbookIndex === 1 ? 'bg-green-500' : 'bg-purple-500'
                      } ${isPositive ? '' : 'bg-opacity-50'}`}
                      style={{ 
                        height: `${Math.max(height, 4)}px`,
                        marginTop: isPositive ? 'auto' : '0'
                      }}
                      title={`${playbook.playbook_name}: ${monthData.return.toFixed(2)}%`}
                    />
                  );
                })}
              </div>
              <div className="text-xs text-gray-600 transform -rotate-45">
                {month.month}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex justify-center space-x-4">
          {comparisonData.performance_comparison.map((playbook, index) => (
            <div key={playbook.playbook_name} className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded ${
                index === 0 ? 'bg-blue-500' :
                index === 1 ? 'bg-green-500' : 'bg-purple-500'
              }`} />
              <span className="text-sm text-gray-600">{playbook.playbook_name}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderRiskAnalysis = () => {
    if (!comparisonData?.risk_analysis) return null;

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {comparisonData.risk_analysis.map((risk, index) => (
          <Card key={risk.playbook_name} className="p-4">
            <h3 className={`font-semibold mb-3 ${
              index === 0 ? 'text-blue-600' :
              index === 1 ? 'text-green-600' : 'text-purple-600'
            }`}>
              {risk.playbook_name} Risk Metrics
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">VaR (95%)</span>
                <span className="font-medium">{(risk.var_95 * 100).toFixed(2)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">VaR (99%)</span>
                <span className="font-medium">{(risk.var_99 * 100).toFixed(2)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Expected Shortfall</span>
                <span className="font-medium">{(risk.expected_shortfall * 100).toFixed(2)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Volatility</span>
                <span className="font-medium">{(risk.volatility * 100).toFixed(2)}%</span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    );
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Playbook Comparison</h1>
        <Button onClick={loadComparisonData} disabled={loading || selectedPlaybooks.length < 2}>
          {loading ? 'Loading...' : 'Refresh Analysis'}
        </Button>
      </div>

      {/* Playbook Selection */}
      <Card className="p-4">
        <h2 className="text-lg font-semibold mb-3">Select Playbooks to Compare</h2>
        <div className="flex flex-wrap gap-2">
          {availablePlaybooks.map(playbook => (
            <button
              key={playbook}
              onClick={() => togglePlaybook(playbook)}
              className={`px-3 py-1 rounded-full text-sm font-medium border ${
                selectedPlaybooks.includes(playbook)
                  ? 'bg-blue-500 text-white border-blue-500'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-blue-500'
              }`}
            >
              {playbook}
            </button>
          ))}
        </div>
        {selectedPlaybooks.length < 2 && (
          <p className="text-sm text-gray-500 mt-2">Select at least 2 playbooks to compare</p>
        )}
      </Card>

      {/* View Mode Tabs */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        {[
          { key: 'metrics', label: 'Key Metrics' },
          { key: 'performance', label: 'Performance' },
          { key: 'risk', label: 'Risk Analysis' }
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setViewMode(key as any)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              viewMode === key
                ? 'bg-white text-blue-600 shadow'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Loading comparison data...</div>
        </div>
      ) : comparisonData ? (
        <div>
          {viewMode === 'metrics' && renderMetricsComparison()}
          {viewMode === 'performance' && renderPerformanceChart()}
          {viewMode === 'risk' && renderRiskAnalysis()}
        </div>
      ) : selectedPlaybooks.length >= 2 ? (
        <div className="text-center text-gray-500 py-8">
          Click "Refresh Analysis" to load comparison data
        </div>
      ) : (
        <div className="text-center text-gray-500 py-8">
          Select at least 2 playbooks to begin comparison
        </div>
      )}
    </div>
  );
};
