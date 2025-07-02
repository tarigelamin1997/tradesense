
import React, { useState, useEffect } from 'react';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import strategyLabService, { 
  SimulationRequest, 
  SimulationResponse, 
  SimulationFilters,
  PlaybookPerformanceComparison,
  WhatIfScenario 
} from '../../../services/strategyLab';
import { playbooksService } from '../../../services/playbooks';

interface StrategyLabDashboardProps {
  className?: string;
}

const StrategyLabDashboard: React.FC<StrategyLabDashboardProps> = ({ className }) => {
  const [activeTab, setActiveTab] = useState<'simulator' | 'playbooks' | 'whatif'>('simulator');
  const [simulation, setSimulation] = useState<SimulationResponse | null>(null);
  const [playbookComparisons, setPlaybookComparisons] = useState<PlaybookPerformanceComparison[]>([]);
  const [whatIfScenarios, setWhatIfScenarios] = useState<WhatIfScenario[]>([]);
  const [availablePlaybooks, setAvailablePlaybooks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Simulation filters state
  const [filters, setFilters] = useState<SimulationFilters>({});
  const [scenarioName, setScenarioName] = useState('');

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [playbooks, comparisons, scenarios] = await Promise.all([
        playbooksService.getPlaybooks(),
        strategyLabService.comparePlaybooks(),
        strategyLabService.getWhatIfScenarios()
      ]);
      
      setAvailablePlaybooks(playbooks);
      setPlaybookComparisons(comparisons);
      setWhatIfScenarios(scenarios);
    } catch (err) {
      setError('Failed to load Strategy Lab data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const runSimulation = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const request: SimulationRequest = {
        filters,
        name: scenarioName || 'Custom Simulation',
        compare_to_baseline: true
      };
      
      const result = await strategyLabService.runSimulation(request);
      setSimulation(result);
    } catch (err) {
      setError('Simulation failed. Please check your filters and try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const applyFilterPreset = (presetName: string) => {
    const presets = strategyLabService.getFilterPresets();
    setFilters(presets[presetName] || {});
    setScenarioName(presetName);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const renderSimulator = () => (
    <div className="space-y-6">
      {/* Filter Controls */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Simulation Filters</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">Scenario Name</label>
            <Input
              value={scenarioName}
              onChange={(e) => setScenarioName(e.target.value)}
              placeholder="Enter scenario name..."
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Min Confidence Score</label>
            <Input
              type="number"
              min="1"
              max="10"
              value={filters.confidence_score_min || ''}
              onChange={(e) => setFilters({...filters, confidence_score_min: parseInt(e.target.value) || undefined})}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Max Confidence Score</label>
            <Input
              type="number"
              min="1"
              max="10"
              value={filters.confidence_score_max || ''}
              onChange={(e) => setFilters({...filters, confidence_score_max: parseInt(e.target.value) || undefined})}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Min P&L</label>
            <Input
              type="number"
              step="0.01"
              value={filters.pnl_min || ''}
              onChange={(e) => setFilters({...filters, pnl_min: parseFloat(e.target.value) || undefined})}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Max P&L</label>
            <Input
              type="number"
              step="0.01"
              value={filters.pnl_max || ''}
              onChange={(e) => setFilters({...filters, pnl_max: parseFloat(e.target.value) || undefined})}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Direction</label>
            <select 
              className="w-full p-2 border border-gray-300 rounded-md"
              value={filters.directions?.[0] || ''}
              onChange={(e) => setFilters({...filters, directions: e.target.value ? [e.target.value] : undefined})}
            >
              <option value="">All Directions</option>
              <option value="long">Long Only</option>
              <option value="short">Short Only</option>
            </select>
          </div>
        </div>

        {/* Filter Presets */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Quick Presets</label>
          <div className="flex flex-wrap gap-2">
            {Object.keys(strategyLabService.getFilterPresets()).map((preset) => (
              <Button
                key={preset}
                size="sm"
                variant="outline"
                onClick={() => applyFilterPreset(preset)}
              >
                {preset}
              </Button>
            ))}
          </div>
        </div>

        <div className="flex gap-2">
          <Button onClick={runSimulation} disabled={loading}>
            {loading ? 'Running Simulation...' : 'Run Simulation'}
          </Button>
          <Button variant="outline" onClick={() => setFilters({})}>
            Clear Filters
          </Button>
        </div>
      </Card>

      {/* Simulation Results */}
      {simulation && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">
            Simulation Results: {simulation.scenario_name}
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {simulation.simulation_metrics.completed_trades}
              </div>
              <div className="text-sm text-gray-600">Trades</div>
            </div>
            
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(simulation.simulation_metrics.total_pnl)}
              </div>
              <div className="text-sm text-gray-600">Total P&L</div>
            </div>
            
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {formatPercentage(simulation.simulation_metrics.win_rate)}
              </div>
              <div className="text-sm text-gray-600">Win Rate</div>
            </div>
            
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {simulation.simulation_metrics.profit_factor?.toFixed(2) || 'N/A'}
              </div>
              <div className="text-sm text-gray-600">Profit Factor</div>
            </div>
          </div>

          {/* Comparison with Baseline */}
          {simulation.comparison && (
            <div className="mb-6">
              <h4 className="font-semibold mb-2">Comparison to Baseline</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className={`p-3 rounded-lg ${simulation.comparison.pnl_improvement_pct > 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                  <div className={`text-lg font-bold ${simulation.comparison.pnl_improvement_pct > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {simulation.comparison.pnl_improvement_pct > 0 ? '+' : ''}{formatPercentage(simulation.comparison.pnl_improvement_pct)}
                  </div>
                  <div className="text-sm text-gray-600">P&L Improvement</div>
                </div>
                
                <div className={`p-3 rounded-lg ${simulation.comparison.win_rate_difference > 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                  <div className={`text-lg font-bold ${simulation.comparison.win_rate_difference > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {simulation.comparison.win_rate_difference > 0 ? '+' : ''}{formatPercentage(simulation.comparison.win_rate_difference)}
                  </div>
                  <div className="text-sm text-gray-600">Win Rate Change</div>
                </div>
                
                <div className="p-3 rounded-lg bg-blue-50">
                  <div className="text-lg font-bold text-blue-600">
                    {simulation.comparison.trade_count_difference > 0 ? '+' : ''}{simulation.comparison.trade_count_difference}
                  </div>
                  <div className="text-sm text-gray-600">Trade Count Diff</div>
                </div>
              </div>
            </div>
          )}

          {/* Insights and Recommendations */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-2">Insights</h4>
              <ul className="space-y-1">
                {simulation.insights.map((insight, index) => (
                  <li key={index} className="text-sm text-gray-700 flex items-start">
                    <span className="text-blue-500 mr-2">•</span>
                    {insight}
                  </li>
                ))}
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Recommendations</h4>
              <ul className="space-y-1">
                {simulation.recommendations.map((rec, index) => (
                  <li key={index} className="text-sm text-gray-700 flex items-start">
                    <span className="text-green-500 mr-2">→</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      )}
    </div>
  );

  const renderPlaybookComparison = () => (
    <div className="space-y-6">
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Playbook Performance Comparison</h3>
        
        {playbookComparisons.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No playbook data available. Create some playbooks and link them to trades to see comparisons.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Playbook</th>
                  <th className="text-right p-3">Trades</th>
                  <th className="text-right p-3">Total P&L</th>
                  <th className="text-right p-3">Win Rate</th>
                  <th className="text-right p-3">Avg P&L</th>
                  <th className="text-right p-3">Profit Factor</th>
                </tr>
              </thead>
              <tbody>
                {playbookComparisons.map((comparison, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-medium">{comparison.playbook_name}</td>
                    <td className="p-3 text-right">{comparison.metrics.completed_trades}</td>
                    <td className={`p-3 text-right font-medium ${comparison.metrics.total_pnl > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(comparison.metrics.total_pnl)}
                    </td>
                    <td className="p-3 text-right">{formatPercentage(comparison.metrics.win_rate)}</td>
                    <td className={`p-3 text-right ${comparison.metrics.avg_pnl > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(comparison.metrics.avg_pnl)}
                    </td>
                    <td className="p-3 text-right">
                      {comparison.metrics.profit_factor?.toFixed(2) || 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );

  const renderWhatIfScenarios = () => (
    <div className="space-y-6">
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">What-If Scenarios</h3>
        
        {whatIfScenarios.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No scenarios available. Add more trade data to generate what-if analyses.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {whatIfScenarios.map((scenario, index) => (
              <Card key={index} className="p-4">
                <h4 className="font-semibold mb-2">{scenario.scenario_name}</h4>
                <p className="text-sm text-gray-600 mb-3">{scenario.description}</p>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm">Total P&L:</span>
                    <span className={`text-sm font-medium ${scenario.metrics.total_pnl > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(scenario.metrics.total_pnl)}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-sm">Win Rate:</span>
                    <span className="text-sm font-medium">{formatPercentage(scenario.metrics.win_rate)}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-sm">Improvement:</span>
                    <span className={`text-sm font-bold ${scenario.improvement_pct > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {scenario.improvement_pct > 0 ? '+' : ''}{formatPercentage(scenario.improvement_pct)}
                    </span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </Card>
    </div>
  );

  if (loading && !simulation) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Strategy Lab...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`strategy-lab-dashboard ${className || ''}`}>
      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { key: 'simulator', label: 'Strategy Simulator' },
            { key: 'playbooks', label: 'Playbook Comparison' },
            { key: 'whatif', label: 'What-If Scenarios' }
          ].map((tab) => (
            <button
              key={tab.key}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab(tab.key as any)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="text-red-800">
              <p className="font-medium">Error</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'simulator' && renderSimulator()}
      {activeTab === 'playbooks' && renderPlaybookComparison()}
      {activeTab === 'whatif' && renderWhatIfScenarios()}
    </div>
  );
};

export default StrategyLabDashboard;
