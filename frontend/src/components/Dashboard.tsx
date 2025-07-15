import { useEffect, useState, useCallback, useRef } from 'react';
import { analyticsService } from '../services/analytics';
import { getTrades } from '../services/trades';
import type { AnalyticsSummary } from '../services/analytics';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area 
} from 'recharts';
import { formatDateRange } from '../utils/date';
import { 
  TrendingUp, TrendingDown, Activity, Award, Calendar, DollarSign, 
  Download, RefreshCw 
} from 'lucide-react';

// Sample data generator for when API fails
const generateSampleData = () => {
  const today = new Date();
  const thirtyDaysAgo = new Date(today);
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
  
  // Generate equity curve
  const equityCurve = [];
  let balance = 10000;
  for (let i = 0; i < 30; i++) {
    const date = new Date(thirtyDaysAgo);
    date.setDate(date.getDate() + i);
    const dailyChange = (Math.random() - 0.45) * 300; // Slight positive bias
    balance += dailyChange;
    equityCurve.push({
      date: date.toISOString().split('T')[0],
      value: Math.round(balance * 100) / 100,
      trades: Math.floor(Math.random() * 5) + 1
    });
  }
  
  // Generate daily P&L for last 14 days
  const dailyPnL = equityCurve.slice(-14).map((point, i, arr) => {
    const prevValue = i === 0 ? 10000 : arr[i - 1].value;
    return {
      date: point.date,
      pnl: Math.round((point.value - prevValue) * 100) / 100,
      trades: point.trades
    };
  });
  
  const totalPnl = balance - 10000;
  const wins = equityCurve.filter((_, i, arr) => i > 0 && arr[i].value > arr[i - 1].value).length;
  const losses = equityCurve.filter((_, i, arr) => i > 0 && arr[i].value < arr[i - 1].value).length;
  
  return {
    stats: {
      totalPnl: Math.round(totalPnl * 100) / 100,
      totalPnlPercent: Math.round((totalPnl / 10000) * 10000) / 100,
      winRate: Math.round((wins / (wins + losses)) * 1000) / 10,
      winRateChange: (Math.random() * 4) - 2,
      totalTrades: 245,
      avgHoldTime: '2h 45m',
      currentStreak: { type: 'win' as const, count: 5 },
      profitFactor: 2.34,
      sharpeRatio: 1.85
    },
    chartData: {
      equityCurve,
      dailyPnL,
      monthlyPnl: [
        { month: 'Oct', pnl: 2840, trades: 78 },
        { month: 'Nov', pnl: 3120, trades: 82 },
        { month: 'Dec', pnl: 1980, trades: 85 }
      ],
      strategyBreakdown: [
        { name: 'Momentum', value: 35, pnl: 5420 },
        { name: 'Mean Reversion', value: 25, pnl: 3180 },
        { name: 'Breakout', value: 40, pnl: 6820 }
      ],
      winDistribution: { wins: 168, losses: 77, breakeven: 0 }
    },
    recentTrades: [
      { 
        id: 1, 
        symbol: 'AAPL', 
        side: 'long',
        entryPrice: 185.50,
        exitPrice: 187.25,
        quantity: 100,
        pnl: 175.00,
        pnlPercent: 0.94,
        entryDate: '2024-01-14 09:30',
        exitDate: '2024-01-14 14:45',
        duration: '5h 15m'
      },
      { 
        id: 2, 
        symbol: 'TSLA', 
        side: 'short',
        entryPrice: 242.80,
        exitPrice: 244.50,
        quantity: 50,
        pnl: -85.00,
        pnlPercent: -0.70,
        entryDate: '2024-01-14 10:15',
        exitDate: '2024-01-14 15:30',
        duration: '5h 15m'
      }
    ]
  };
};

interface DashboardStats {
  totalPnl: number;
  totalPnlPercent: number;
  winRate: number;
  winRateChange: number;
  totalTrades: number;
  avgHoldTime: string;
  currentStreak: { type: 'win' | 'loss'; count: number };
  profitFactor: number;
  sharpeRatio: number;
}

const COLORS = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444'];

function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    totalPnl: 0,
    totalPnlPercent: 0,
    winRate: 0,
    winRateChange: 0,
    totalTrades: 0,
    avgHoldTime: '0h',
    currentStreak: { type: 'win', count: 0 },
    profitFactor: 0,
    sharpeRatio: 0
  });
  
  const [chartData, setChartData] = useState<any>({
    equityCurve: [],
    dailyPnL: [],
    monthlyPnl: [],
    strategyBreakdown: []
  });
  
  const [recentTrades, setRecentTrades] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [dateRange, setDateRange] = useState(30);
  const [usingSampleData, setUsingSampleData] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      if (!loading) setIsRefreshing(true);
      
      // For now, just use sample data
      const sampleData = generateSampleData();
      setStats(sampleData.stats);
      setChartData(sampleData.chartData);
      setRecentTrades(sampleData.recentTrades);
      setUsingSampleData(true);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [loading]);

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  const formatCurrency = (amount: number) => {
    const formatted = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(Math.abs(amount));
    return amount >= 0 ? formatted : `-${formatted}`;
  };

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length > 0) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm text-gray-600">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm font-medium" style={{ color: entry.color }}>
              {entry.name}: {entry.name.includes('P&L') || entry.name.includes('Value') || entry.name.includes('pnl')
                ? formatCurrency(entry.value) 
                : entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6 animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm p-6">
              <div className="h-4 bg-gray-200 rounded w-20 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-32 mb-4"></div>
              <div className="h-3 bg-gray-200 rounded w-16"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Trading Dashboard</h1>
              <p className="text-gray-600 mt-1">
                {usingSampleData ? 'Demo Data' : `Performance for ${dateRange} days`}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <select 
                value={dateRange}
                onChange={(e) => setDateRange(Number(e.target.value))}
                className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={365}>Last year</option>
              </select>
              
              <button
                onClick={fetchData}
                disabled={isRefreshing}
                className="p-2 bg-white border border-gray-200 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`h-5 w-5 ${isRefreshing ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>

        {/* Hero Metrics Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {/* Total P&L Card */}
          <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Total P&L</h3>
              <DollarSign className="w-5 h-5 text-gray-400" />
            </div>
            <div className="space-y-1">
              <p className={`text-2xl font-bold ${stats.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(stats.totalPnl)}
              </p>
              <div className="flex items-center gap-1">
                {stats.totalPnlPercent >= 0 ? (
                  <TrendingUp className="w-4 h-4 text-green-500" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-500" />
                )}
                <span className={`text-sm font-medium ${stats.totalPnlPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {Math.abs(stats.totalPnlPercent).toFixed(1)}%
                </span>
                <span className="text-sm text-gray-500">vs last period</span>
              </div>
            </div>
          </div>

          {/* Win Rate Card */}
          <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Win Rate</h3>
              <Activity className="w-5 h-5 text-gray-400" />
            </div>
            <div className="space-y-1">
              <p className="text-2xl font-bold text-gray-900">{stats.winRate.toFixed(1)}%</p>
              <div className="flex items-center gap-1">
                {stats.winRateChange >= 0 ? (
                  <TrendingUp className="w-4 h-4 text-green-500" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-500" />
                )}
                <span className={`text-sm font-medium ${stats.winRateChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {Math.abs(stats.winRateChange).toFixed(1)}%
                </span>
                <span className="text-sm text-gray-500">vs last period</span>
              </div>
            </div>
          </div>

          {/* Total Trades Card */}
          <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Total Trades</h3>
              <Calendar className="w-5 h-5 text-gray-400" />
            </div>
            <div className="space-y-1">
              <p className="text-2xl font-bold text-gray-900">{stats.totalTrades}</p>
              <p className="text-sm text-gray-500">
                This {dateRange === 7 ? 'week' : dateRange === 30 ? 'month' : 'period'}
              </p>
            </div>
          </div>

          {/* Current Streak Card */}
          <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Current Streak</h3>
              <Award className="w-5 h-5 text-gray-400" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-2xl">🔥</span>
                <p className="text-2xl font-bold text-gray-900">{stats.currentStreak.count}</p>
                <span className="text-lg font-medium text-gray-600 capitalize">{stats.currentStreak.type}s</span>
              </div>
              <p className="text-sm text-gray-500">Keep it going!</p>
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Equity Curve */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Equity Curve</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData.equityCurve}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis tickFormatter={(value) => `$${value}`} />
                <Tooltip content={<CustomTooltip />} />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#10B981" 
                  fillOpacity={1} 
                  fill="url(#colorValue)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Daily P&L */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily P&L</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData.dailyPnL}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis tickFormatter={(value) => `$${value}`} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="pnl" fill={(entry: any) => entry.pnl >= 0 ? '#10B981' : '#EF4444'} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Trades Table */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Trades</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Side</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entry</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Exit</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {recentTrades.map((trade) => (
                  <tr key={trade.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{trade.symbol}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className={`inline-flex px-2 text-xs leading-5 font-semibold rounded-full ${
                        trade.side === 'long' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {trade.side}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${trade.entryPrice}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${trade.exitPrice}</td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                      trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(trade.pnl)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{trade.duration}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;