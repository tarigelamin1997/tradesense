
import React, { useState, useEffect } from 'react';
import { Card } from '../../../components/ui/Card.tsx';
import { playbooksService } from '../../../services/playbooks.ts';

interface PlaybookMetrics {
  playbook_id: string;
  playbook_name: string;
  total_trades: number;
  win_rate: number;
  avg_return: number;
  total_pnl: number;
  sharpe_ratio: number;
  max_drawdown: number;
  profit_factor: number;
  expectancy: number;
  avg_win: number;
  avg_loss: number;
  largest_win: number;
  largest_loss: number;
}

interface ComparisonData {
  playbooks: PlaybookMetrics[];
  comparison_matrix: {
    metric: string;
    values: { [playbook_name: string]: number };
  }[];
}

export const PlaybookComparisonDashboard: React.FC = () => {
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [selectedPlaybooks, setSelectedPlaybooks] = useState<string[]>([]);
  const [availablePlaybooks, setAvailablePlaybooks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState('win_rate');

  useEffect(() => {
    loadAvailablePlaybooks();
  }, []);

  const loadAvailablePlaybooks = async () => {
    try {
      const playbooks = await playbooksService.getPlaybooks();
      setAvailablePlaybooks(playbooks);
      if (playbooks.length >= 2) {
        setSelectedPlaybooks(playbooks.slice(0, 2).map((p: any) => p.id));
      }
    } catch (error) {
      console.error('Failed to load playbooks:', error);
    }
  };

  const loadComparisonData = async () => {
    if (selectedPlaybooks.length < 2) return;
    
    setLoading(true);
    try {
      const response = await playbooksService.comparePlaybooks(selectedPlaybooks);
      setComparisonData(response);
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

  const handlePlaybookToggle = (playbookId: string) => {
    setSelectedPlaybooks(prev => {
      if (prev.includes(playbookId)) {
        return prev.filter(id => id !== playbookId);
      } else {
        return [...prev, playbookId];
      }
    });
  };

  const getMetricColor = (value: number, metric: string) => {
    const isPositiveMetric = ['win_rate', 'avg_return', 'total_pnl', 'sharpe_ratio', 'profit_factor', 'expectancy'].includes(metric);
    const isNegativeMetric = ['max_drawdown', 'avg_loss', 'largest_loss'].includes(metric);
    
    if (isPositiveMetric) {
      return value > 0 ? 'text-green-600' : 'text-red-600';
    } else if (isNegativeMetric) {
      return value < 0 ? 'text-red-600' : 'text-green-600';
    }
    return 'text-gray-600';
  };

  const formatMetricValue = (value: number, metric: string) => {
    if (metric.includes('rate')) {
      return `${(value * 100).toFixed(1)}%`;
    } else if (metric.includes('pnl') || metric.includes('return') || metric.includes('win') || metric.includes('loss')) {
      return `$${value.toFixed(2)}`;
    } else if (metric === 'sharpe_ratio' || metric === 'profit_factor') {
      return value.toFixed(2);
    }
    return value.toFixed(1);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading comparison data...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Playbook Selection */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Select Playbooks to Compare</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {availablePlaybooks.map((playbook) => (
            <label key={playbook.id} className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedPlaybooks.includes(playbook.id)}
                onChange={() => handlePlaybookToggle(playbook.id)}
                className="rounded border-gray-300"
              />
              <span className="text-sm">{playbook.name}</span>
            </label>
          ))}
        </div>
      </Card>

      {comparisonData && (
        <>
          {/* Summary Comparison Table */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Performance Comparison</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Metric</th>
                    {comparisonData.playbooks.map((playbook) => (
                      <th key={playbook.playbook_id} className="text-right py-2">
                        {playbook.playbook_name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { key: 'total_trades', label: 'Total Trades' },
                    { key: 'win_rate', label: 'Win Rate' },
                    { key: 'total_pnl', label: 'Total P&L' },
                    { key: 'avg_return', label: 'Avg Return' },
                    { key: 'sharpe_ratio', label: 'Sharpe Ratio' },
                    { key: 'profit_factor', label: 'Profit Factor' },
                    { key: 'max_drawdown', label: 'Max Drawdown' },
                    { key: 'expectancy', label: 'Expectancy' }
                  ].map((metric) => (
                    <tr key={metric.key} className="border-b">
                      <td className="py-2 font-medium">{metric.label}</td>
                      {comparisonData.playbooks.map((playbook) => (
                        <td key={playbook.playbook_id} className="text-right py-2">
                          <span className={getMetricColor(playbook[metric.key as keyof PlaybookMetrics] as number, metric.key)}>
                            {formatMetricValue(playbook[metric.key as keyof PlaybookMetrics] as number, metric.key)}
                          </span>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Visual Comparison Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Win Rate vs Return Scatter */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Risk vs Return</h3>
              <div className="h-64 flex items-center justify-center border rounded">
                <div className="text-center">
                  <div className="text-4xl mb-2">📊</div>
                  <div className="text-sm text-gray-600">
                    Scatter plot: Win Rate vs Average Return
                  </div>
                  <div className="mt-4 space-y-2">
                    {comparisonData.playbooks.map((playbook, index) => (
                      <div key={playbook.playbook_id} className="flex justify-between text-xs">
                        <span>{playbook.playbook_name}</span>
                        <span>
                          {(playbook.win_rate * 100).toFixed(1)}% / ${playbook.avg_return.toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>

            {/* Profit Factor Comparison */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Profit Factor Comparison</h3>
              <div className="h-64 space-y-4">
                {comparisonData.playbooks.map((playbook, index) => (
                  <div key={playbook.playbook_id} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>{playbook.playbook_name}</span>
                      <span className="font-medium">{playbook.profit_factor.toFixed(2)}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          playbook.profit_factor > 1.5 ? 'bg-green-500' :
                          playbook.profit_factor > 1.0 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.min(playbook.profit_factor * 25, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Trade Count Distribution */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Trade Volume</h3>
              <div className="h-64 space-y-4">
                {comparisonData.playbooks.map((playbook) => (
                  <div key={playbook.playbook_id} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>{playbook.playbook_name}</span>
                      <span className="font-medium">{playbook.total_trades} trades</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-blue-500 h-3 rounded-full"
                        style={{ 
                          width: `${(playbook.total_trades / Math.max(...comparisonData.playbooks.map(p => p.total_trades))) * 100}%` 
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Sharpe Ratio Comparison */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Risk-Adjusted Returns</h3>
              <div className="h-64 space-y-4">
                {comparisonData.playbooks.map((playbook) => (
                  <div key={playbook.playbook_id} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>{playbook.playbook_name}</span>
                      <span className={`font-medium ${getMetricColor(playbook.sharpe_ratio, 'sharpe_ratio')}`}>
                        {playbook.sharpe_ratio.toFixed(2)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          playbook.sharpe_ratio > 1.0 ? 'bg-green-500' :
                          playbook.sharpe_ratio > 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.max((playbook.sharpe_ratio + 1) * 25, 5)}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Winner Analysis */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Performance Rankings</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { metric: 'total_pnl', label: 'Total P&L', format: '$' },
                { metric: 'win_rate', label: 'Win Rate', format: '%' },
                { metric: 'sharpe_ratio', label: 'Sharpe Ratio', format: '' },
                { metric: 'profit_factor', label: 'Profit Factor', format: '' }
              ].map((ranking) => {
                const sorted = [...comparisonData.playbooks].sort((a, b) => 
                  (b[ranking.metric as keyof PlaybookMetrics] as number) - (a[ranking.metric as keyof PlaybookMetrics] as number)
                );
                
                return (
                  <div key={ranking.metric} className="space-y-2">
                    <h4 className="font-medium text-sm text-gray-700">{ranking.label} Leader</h4>
                    <div className="space-y-1">
                      {sorted.slice(0, 3).map((playbook, index) => (
                        <div key={playbook.playbook_id} className="flex justify-between text-sm">
                          <span className="truncate">
                            {index === 0 && '🥇'} {index === 1 && '🥈'} {index === 2 && '🥉'} {playbook.playbook_name}
                          </span>
                          <span className="font-medium ml-2">
                            {ranking.format === '$' && '$'}
                            {(playbook[ranking.metric as keyof PlaybookMetrics] as number * 
                              (ranking.format === '%' ? 100 : 1)).toFixed(ranking.format === '$' ? 2 : 1)}
                            {ranking.format === '%' && '%'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </>
      )}

      {selectedPlaybooks.length < 2 && (
        <Card className="p-8 text-center">
          <div className="text-4xl mb-4">📊</div>
          <h3 className="text-lg font-semibold mb-2">Select Multiple Playbooks</h3>
          <p className="text-gray-600">Choose at least 2 playbooks to see comparison charts and analytics.</p>
        </Card>
      )}
    </div>
  );
};
