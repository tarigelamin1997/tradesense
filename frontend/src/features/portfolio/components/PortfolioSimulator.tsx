
import React, { useState, useEffect } from 'react';
import { portfolioService, Portfolio, EquityDataPoint } from '../../../services/portfolio';
import { tradesService } from '../../../services/trades';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export const PortfolioSimulator: React.FC = () => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [equityData, setEquityData] = useState<EquityDataPoint[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newPortfolio, setNewPortfolio] = useState({ name: '', initial_balance: 10000 });
  const [selectedTrades, setSelectedTrades] = useState<string[]>([]);
  const [availableTrades, setAvailableTrades] = useState<any[]>([]);

  useEffect(() => {
    loadPortfolios();
    loadTrades();
  }, []);

  const loadPortfolios = async () => {
    try {
      const data = await portfolioService.getPortfolios();
      setPortfolios(data);
      if (data.length > 0 && !selectedPortfolio) {
        setSelectedPortfolio(data[0]);
        loadEquityCurve(data[0].id);
      }
    } catch (error) {
      console.error('Error loading portfolios:', error);
    }
  };

  const loadTrades = async () => {
    try {
      const trades = await tradesService.getTrades();
      setAvailableTrades(trades.filter((trade: any) => trade.pnl !== null));
    } catch (error) {
      console.error('Error loading trades:', error);
    }
  };

  const loadEquityCurve = async (portfolioId: string) => {
    try {
      setLoading(true);
      const response = await portfolioService.getEquityCurve(portfolioId);
      setEquityData(response.equity_curve);
      setMetrics(response.metrics);
    } catch (error) {
      console.error('Error loading equity curve:', error);
      setEquityData([]);
      setMetrics(null);
    } finally {
      setLoading(false);
    }
  };

  const createPortfolio = async () => {
    try {
      await portfolioService.createPortfolio(newPortfolio);
      setNewPortfolio({ name: '', initial_balance: 10000 });
      setShowCreateForm(false);
      loadPortfolios();
    } catch (error) {
      console.error('Error creating portfolio:', error);
    }
  };

  const simulateTrades = async () => {
    if (!selectedPortfolio || selectedTrades.length === 0) return;

    try {
      setLoading(true);
      await portfolioService.simulateTrades(selectedPortfolio.id, selectedTrades);
      await loadPortfolios();
      await loadEquityCurve(selectedPortfolio.id);
    } catch (error) {
      console.error('Error simulating trades:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartData = {
    labels: equityData.map(point => new Date(point.date).toLocaleDateString()),
    datasets: [
      {
        label: 'Portfolio Balance',
        data: equityData.map(point => point.balance),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Portfolio Equity Curve',
      },
    },
    scales: {
      y: {
        beginAtZero: false,
        ticks: {
          callback: function(value: any) {
            return '$' + value.toLocaleString();
          }
        }
      }
    },
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Portfolio Simulator</h1>
        <Button onClick={() => setShowCreateForm(true)}>
          Create New Portfolio
        </Button>
      </div>

      {/* Create Portfolio Form */}
      {showCreateForm && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Create New Portfolio</h3>
          <div className="space-y-4">
            <Input
              placeholder="Portfolio Name"
              value={newPortfolio.name}
              onChange={(e) => setNewPortfolio({ ...newPortfolio, name: e.target.value })}
            />
            <Input
              type="number"
              placeholder="Initial Balance"
              value={newPortfolio.initial_balance}
              onChange={(e) => setNewPortfolio({ ...newPortfolio, initial_balance: Number(e.target.value) })}
            />
            <div className="flex space-x-2">
              <Button onClick={createPortfolio}>Create</Button>
              <Button variant="outline" onClick={() => setShowCreateForm(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Portfolio Selection */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Select Portfolio</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {portfolios.map((portfolio) => (
            <div
              key={portfolio.id}
              className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                selectedPortfolio?.id === portfolio.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => {
                setSelectedPortfolio(portfolio);
                loadEquityCurve(portfolio.id);
              }}
            >
              <h4 className="font-semibold">{portfolio.name}</h4>
              <p className="text-sm text-gray-600">
                Balance: ${portfolio.current_balance.toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">
                P&L: ${portfolio.total_pnl.toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">
                Return: {portfolio.return_percentage.toFixed(2)}%
              </p>
            </div>
          ))}
        </div>
      </Card>

      {/* Trade Selection */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Select Trades to Simulate</h3>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          <div className="flex items-center space-x-2 mb-2">
            <input
              type="checkbox"
              id="select-all"
              checked={selectedTrades.length === availableTrades.length}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedTrades(availableTrades.map(trade => trade.id));
                } else {
                  setSelectedTrades([]);
                }
              }}
            />
            <label htmlFor="select-all" className="font-medium">Select All</label>
          </div>
          {availableTrades.map((trade) => (
            <div key={trade.id} className="flex items-center space-x-2">
              <input
                type="checkbox"
                id={trade.id}
                checked={selectedTrades.includes(trade.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedTrades([...selectedTrades, trade.id]);
                  } else {
                    setSelectedTrades(selectedTrades.filter(id => id !== trade.id));
                  }
                }}
              />
              <label htmlFor={trade.id} className="text-sm">
                {trade.symbol} - {new Date(trade.entry_time).toLocaleDateString()} - 
                P&L: ${trade.pnl?.toFixed(2)} ({trade.pnl > 0 ? '+' : ''}{((trade.pnl / (trade.entry_price * trade.quantity)) * 100).toFixed(2)}%)
              </label>
            </div>
          ))}
        </div>
        <Button 
          onClick={simulateTrades} 
          disabled={!selectedPortfolio || selectedTrades.length === 0 || loading}
          className="mt-4"
        >
          {loading ? 'Simulating...' : 'Run Simulation'}
        </Button>
      </Card>

      {/* Portfolio Metrics */}
      {selectedPortfolio && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-4">
            <h4 className="font-semibold text-gray-600">Current Balance</h4>
            <p className="text-2xl font-bold">${selectedPortfolio.current_balance.toLocaleString()}</p>
          </Card>
          <Card className="p-4">
            <h4 className="font-semibold text-gray-600">Total P&L</h4>
            <p className={`text-2xl font-bold ${selectedPortfolio.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${selectedPortfolio.total_pnl.toLocaleString()}
            </p>
          </Card>
          <Card className="p-4">
            <h4 className="font-semibold text-gray-600">Win Rate</h4>
            <p className="text-2xl font-bold">{selectedPortfolio.win_rate.toFixed(1)}%</p>
          </Card>
          <Card className="p-4">
            <h4 className="font-semibold text-gray-600">Total Return</h4>
            <p className={`text-2xl font-bold ${selectedPortfolio.return_percentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {selectedPortfolio.return_percentage.toFixed(2)}%
            </p>
          </Card>
        </div>
      )}

      {/* Advanced Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-4">
            <h4 className="font-semibold text-gray-600">Sharpe Ratio</h4>
            <p className="text-2xl font-bold">{metrics.sharpe_ratio.toFixed(3)}</p>
          </Card>
          <Card className="p-4">
            <h4 className="font-semibold text-gray-600">Max Drawdown</h4>
            <p className="text-2xl font-bold text-red-600">{metrics.max_drawdown.toFixed(2)}%</p>
          </Card>
          <Card className="p-4">
            <h4 className="font-semibold text-gray-600">Total Return</h4>
            <p className={`text-2xl font-bold ${metrics.total_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {metrics.total_return.toFixed(2)}%
            </p>
          </Card>
        </div>
      )}

      {/* Equity Curve Chart */}
      {equityData.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Equity Curve</h3>
          <div className="h-96">
            <Line data={chartData} options={chartOptions} />
          </div>
        </Card>
      )}
    </div>
  );
};
