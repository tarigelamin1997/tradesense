
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { patternsService, PatternCluster, PatternInsights, AnalysisStatus } from '../../../services/patterns';

const PatternExplorer: React.FC = () => {
  const [clusters, setClusters] = useState<PatternCluster[]>([]);
  const [insights, setInsights] = useState<PatternInsights | null>(null);
  const [status, setStatus] = useState<AnalysisStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [filters, setFilters] = useState({
    cluster_type: '',
    min_avg_return: undefined as number | undefined,
    saved_only: false,
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadClusters();
  }, [filters]);

  const loadData = async () => {
    try {
      const [statusData, insightsData] = await Promise.all([
        patternsService.getAnalysisStatus(),
        patternsService.getPatternInsights().catch(() => null),
      ]);
      
      setStatus(statusData);
      setInsights(insightsData);
      
      if (statusData.status === 'completed') {
        loadClusters();
      }
    } catch (error) {
      console.error('Error loading pattern data:', error);
    }
  };

  const loadClusters = async () => {
    try {
      setLoading(true);
      const clustersData = await patternsService.getPatternClusters(filters);
      setClusters(clustersData);
    } catch (error) {
      console.error('Error loading clusters:', error);
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async () => {
    try {
      setAnalyzing(true);
      await patternsService.analyzePatterns(20);
      
      // Poll for completion
      const pollInterval = setInterval(async () => {
        const newStatus = await patternsService.getAnalysisStatus();
        setStatus(newStatus);
        
        if (newStatus.status === 'completed') {
          clearInterval(pollInterval);
          setAnalyzing(false);
          loadData();
        }
      }, 5000);
      
      setTimeout(() => {
        clearInterval(pollInterval);
        setAnalyzing(false);
      }, 300000); // Stop polling after 5 minutes
      
    } catch (error) {
      console.error('Error running analysis:', error);
      setAnalyzing(false);
    }
  };

  const saveToPlaybook = async (clusterId: string) => {
    try {
      await patternsService.saveToPlaybook(clusterId);
      loadClusters(); // Refresh to show updated status
    } catch (error) {
      console.error('Error saving to playbook:', error);
    }
  };

  const formatPnL = (value: number) => {
    return value >= 0 ? `+$${value.toFixed(2)}` : `-$${Math.abs(value).toFixed(2)}`;
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const getPatternIcon = (avgReturn: number) => {
    if (avgReturn > 0) return '🟩';
    if (avgReturn < 0) return '🔻';
    return '⚪';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Pattern Explorer</h1>
          <p className="text-gray-600 mt-1">
            AI-powered detection of your trading patterns and edge opportunities
          </p>
        </div>
        
        <Button
          onClick={runAnalysis}
          disabled={analyzing}
          className="bg-blue-600 text-white hover:bg-blue-700"
        >
          {analyzing ? 'Analyzing...' : 'Run Analysis'}
        </Button>
      </div>

      {/* Status Card */}
      {status && (
        <Card>
          <CardHeader>
            <CardTitle>Analysis Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{status.message}</p>
                {status.last_analysis && (
                  <p className="text-xs text-gray-500 mt-1">
                    Last analysis: {new Date(status.last_analysis).toLocaleDateString()}
                  </p>
                )}
              </div>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                status.status === 'completed' ? 'bg-green-100 text-green-800' :
                status.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {status.status}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Insights Overview */}
      {insights && (
        <Card>
          <CardHeader>
            <CardTitle>Pattern Insights</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{insights.total_patterns}</div>
                <div className="text-sm text-gray-600">Total Patterns</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{insights.profitable_patterns}</div>
                <div className="text-sm text-gray-600">Profitable</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{insights.losing_patterns}</div>
                <div className="text-sm text-gray-600">Losing</div>
              </div>
            </div>
            
            <div className="space-y-2">
              {insights.insights.map((insight, index) => (
                <p key={index} className="text-sm text-gray-700">• {insight}</p>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type
              </label>
              <select
                value={filters.cluster_type}
                onChange={(e) => setFilters({...filters, cluster_type: e.target.value})}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="">All Types</option>
                <option value="performance">Performance</option>
                <option value="behavioral">Behavioral</option>
                <option value="temporal">Temporal</option>
                <option value="setup">Setup</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min Return
              </label>
              <input
                type="number"
                step="0.01"
                value={filters.min_avg_return || ''}
                onChange={(e) => setFilters({
                  ...filters, 
                  min_avg_return: e.target.value ? parseFloat(e.target.value) : undefined
                })}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm w-32"
                placeholder="0.00"
              />
            </div>
            
            <div className="flex items-end">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.saved_only}
                  onChange={(e) => setFilters({...filters, saved_only: e.target.checked})}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Saved Only</span>
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pattern Clusters */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {loading ? (
          <div className="col-span-full text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading patterns...</p>
          </div>
        ) : clusters.length === 0 ? (
          <div className="col-span-full text-center py-8">
            <p className="text-gray-600">
              {status?.status === 'completed' ? 'No patterns found with current filters.' : 'Run pattern analysis to discover your trading patterns.'}
            </p>
          </div>
        ) : (
          clusters.map((cluster) => (
            <Card key={cluster.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center">
                    <span className="mr-2">{getPatternIcon(cluster.avg_return)}</span>
                    {cluster.name}
                  </span>
                  {cluster.is_saved_to_playbook === "true" && (
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                      Saved
                    </span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">{cluster.summary}</p>
                
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <div className="text-lg font-semibold text-gray-900">
                      {formatPnL(cluster.avg_return)}
                    </div>
                    <div className="text-xs text-gray-500">Avg Return</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-gray-900">
                      {formatPercentage(cluster.win_rate)}
                    </div>
                    <div className="text-xs text-gray-500">Win Rate</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-gray-900">
                      {cluster.trade_count}
                    </div>
                    <div className="text-xs text-gray-500">Trades</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-gray-900">
                      {formatPnL(cluster.total_pnl)}
                    </div>
                    <div className="text-xs text-gray-500">Total P&L</div>
                  </div>
                </div>

                {/* Key Features */}
                <div className="mb-4">
                  <div className="text-xs font-medium text-gray-700 mb-2">Key Features:</div>
                  <div className="flex flex-wrap gap-1">
                    {cluster.dominant_instrument && (
                      <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                        {cluster.dominant_instrument}
                      </span>
                    )}
                    {cluster.dominant_time_window && (
                      <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                        {cluster.dominant_time_window}
                      </span>
                    )}
                    {cluster.dominant_mood && cluster.dominant_mood !== 'neutral' && (
                      <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                        {cluster.dominant_mood}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex gap-2">
                  {cluster.is_saved_to_playbook !== "true" && (
                    <Button
                      size="sm"
                      onClick={() => saveToPlaybook(cluster.id)}
                      className="bg-green-600 text-white hover:bg-green-700"
                    >
                      Save to Playbook
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      // TODO: Navigate to detailed view
                      console.log('View details for cluster:', cluster.id);
                    }}
                  >
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default PatternExplorer;
