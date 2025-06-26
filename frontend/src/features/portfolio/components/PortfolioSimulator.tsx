
import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { portfolioService } from '../../../services/portfolio';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface Portfolio {
  id: string;
  name: string;
  initial_balance: number;
  current_balance: number;
  total_pnl: number;
  total_trades: number;
  winning_trades: number;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

interface EquityPoint {
  timestamp: string;
  balance: number;
  daily_pnl: number;
  total_pnl: number;
  trade_count: number;
}

const PortfolioSimulator: React.FC = () => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [equityCurve, setEquityCurve] = useState<EquityPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState('');
  const [newPortfolioBalance, setNewPortfolioBalance] = useState(10000);

  useEffect(() => {
    loadPortfolios();
  }, []);

  const loadPortfolios = async () => {
    try {
      setLoading(true);
      const data = await portfolioService.getPortfolios();
      setPortfolios(data);
      
      // Auto-select default portfolio or first one
      const defaultPortfolio = data.find(p => p.is_default) || data[0];
      if (defaultPortfolio) {
        setSelectedPortfolio(defaultPortfolio);
        await loadEquityCurve(defaultPortfolio.id);
      }
    } catch (err) {
      setError('Failed to load portfolios');
      console.error('Portfolio loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadEquityCurve = async (portfolioId: string) => {
    try {
      const data = await portfolioService.getEquityCurve(portfolioId);
      setEquityCurve(data);
    } catch (err) {
      console.error('Failed to load equity curve:', err);
    }
  };

  const createPortfolio = async () => {
    if (!newPortfolioName.trim()) {
      setError('Portfolio name is required');
      return;
    }

    try {
      setLoading(true);
      const result = await portfolioService.createPortfolio({
        name: newPortfolioName,
        initial_balance: newPortfolioBalance
      });

      if (result.success) {
        setShowCreateForm(false);
        setNewPortfolioName('');
        setNewPortfolioBalance(10000);
        await loadPortfolios();
      } else {
        setError(result.error || 'Failed to create portfolio');
      }
    } catch (err) {
      setError('Failed to create portfolio');
    } finally {
      setLoading(false);
    }
  };

  const simulateTrade = async (tradeData: any) => {
    if (!selectedPortfolio) return;

    try {
      setLoading(true);
      await portfolioService.simulateTrade(selectedPortfolio.id, tradeData);
      await loadPortfolios();
      await loadEquityCurve(selectedPortfolio.id);
    } catch (err) {
      setError('Failed to simulate trade');
    } finally {
      setLoading(false);
    }
  };

  const getChartData = () => {
    if (!equityCurve.length) return null;

    const labels = equityCurve.map(point => 
      new Date(point.timestamp).toLocaleDateString()
    );
    
    const balanceData = equityCurve.map(point => point.balance);
    const pnlData = equityCurve.map(point => point.total_pnl);

    return {
      labels,
      datasets: [
        {
          label: 'Portfolio Balance',
          data: balanceData,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.1,
        },
        {
          label: 'Total P&L',
          data: pnlData,
          borderColor: pnlData[pnlData.length - 1] >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
          backgroundColor: pnlData[pnlData.length - 1] >= 0 ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          fill: false,
          tension: 0.1,
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Portfolio Performance Over Time',
      },
    },
    scales: {
      y: {
        beginAtZero: false,
        title: {
          display: true,
          text: 'Value ($)',
        },
      },
    },
  };

  const calculateWinRate = (portfolio: Portfolio) => {
    return portfolio.total_trades > 0 ? 
      ((portfolio.winning_trades / portfolio.total_trades) * 100).toFixed(1) : '0.0';
  };

  const calculateROI = (portfolio: Portfolio) => {
    return portfolio.initial_balance > 0 ? 
      (((portfolio.current_balance - portfolio.initial_balance) / portfolio.initial_balance) * 100).toFixed(2) : '0.00';
  };

  if (loading && portfolios.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Portfolio Simulator</h1>
        <Button 
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 hover:bg-blue-700"
        >
          Create Portfolio
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
          <button 
            onClick={() => setError(null)}
            className="float-right text-red-400 hover:text-red-600"
          >
            ×
          </button>
        </div>
      )}

      {/* Create Portfolio Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Create New Portfolio</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Portfolio Name
                  </label>
                  <Input
                    value={newPortfolioName}
                    onChange={(e) => setNewPortfolioName(e.target.value)}
                    placeholder="My Trading Portfolio"
                    className="w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Initial Balance ($)
                  </label>
                  <Input
                    type="number"
                    value={newPortfolioBalance}
                    onChange={(e) => setNewPortfolioBalance(Number(e.target.value))}
                    min="1000"
                    step="1000"
                    className="w-full"
                  />
                </div>
              </div>

              <div className="flex space-x-3 mt-6">
                <Button
                  onClick={() => setShowCreateForm(false)}
                  variant="secondary"
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={createPortfolio}
                  disabled={loading}
                  className="flex-1"
                >
                  {loading ? 'Creating...' : 'Create'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Portfolio Selection */}
      {portfolios.length > 0 && (
        <Card>
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Select Portfolio</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {portfolios.map((portfolio) => (
                <div
                  key={portfolio.id}
                  onClick={() => {
                    setSelectedPortfolio(portfolio);
                    loadEquityCurve(portfolio.id);
                  }}
                  className={`cursor-pointer p-4 border rounded-lg transition-colors ${
                    selectedPortfolio?.id === portfolio.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium">{portfolio.name}</h3>
                    {portfolio.is_default && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        Default
                      </span>
                    )}
                  </div>
                  
                  <div className="space-y-1 text-sm text-gray-600">
                    <p>Balance: ${portfolio.current_balance.toLocaleString()}</p>
                    <p>P&L: <span className={portfolio.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                      ${portfolio.total_pnl.toLocaleString()}
                    </span></p>
                    <p>Trades: {portfolio.total_trades}</p>
                    <p>Win Rate: {calculateWinRate(portfolio)}%</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Portfolio Details & Equity Curve */}
      {selectedPortfolio && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Performance Metrics */}
          <Card>
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Performance Metrics</h3>
              
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-600">Current Balance:</span>
                  <span className="font-semibold">
                    ${selectedPortfolio.current_balance.toLocaleString()}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Initial Balance:</span>
                  <span>${selectedPortfolio.initial_balance.toLocaleString()}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Total P&L:</span>
                  <span className={selectedPortfolio.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                    ${selectedPortfolio.total_pnl.toLocaleString()}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">ROI:</span>
                  <span className={selectedPortfolio.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {calculateROI(selectedPortfolio)}%
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Trades:</span>
                  <span>{selectedPortfolio.total_trades}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Winning Trades:</span>
                  <span>{selectedPortfolio.winning_trades}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Win Rate:</span>
                  <span>{calculateWinRate(selectedPortfolio)}%</span>
                </div>
              </div>
            </div>
          </Card>

          {/* Equity Curve Chart */}
          <div className="lg:col-span-2">
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4">Equity Curve</h3>
                
                {equityCurve.length > 0 ? (
                  <div className="h-96">
                    <Line data={getChartData()!} options={chartOptions} />
                  </div>
                ) : (
                  <div className="h-96 flex items-center justify-center text-gray-500">
                    <div className="text-center">
                      <p>No equity data available</p>
                      <p className="text-sm mt-2">Start trading to see your portfolio performance</p>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>
      )}

      {portfolios.length === 0 && !loading && (
        <Card>
          <div className="p-12 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Portfolios Found</h3>
            <p className="text-gray-600 mb-6">
              Create your first virtual portfolio to start tracking your trading performance.
            </p>
            <Button 
              onClick={() => setShowCreateForm(true)}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Create Your First Portfolio
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
};

export default PortfolioSimulator;
