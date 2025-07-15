import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity, 
  Target,
  Award,
  AlertTriangle,
  Zap
} from 'lucide-react';
import { Card, CardContent } from './ui/Card';

interface Trade {
  id: number;
  pnl: number;
  pnl_percentage: number;
  status: 'open' | 'closed';
}

interface TradeStatisticsProps {
  trades: Trade[];
  loading?: boolean;
}

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: 'green' | 'red' | 'blue' | 'gray';
  subtitle?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, color, subtitle }) => {
  const colorClasses = {
    green: 'text-green-600 bg-green-100',
    red: 'text-red-600 bg-red-100',
    blue: 'text-blue-600 bg-blue-100',
    gray: 'text-gray-600 bg-gray-100'
  };

  const textColorClasses = {
    green: 'text-green-600',
    red: 'text-red-600',
    blue: 'text-blue-600',
    gray: 'text-gray-900'
  };

  return (
    <Card className="relative overflow-hidden" padding="sm">
      <CardContent>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className={`text-2xl font-bold mt-1 ${textColorClasses[color]}`}>
              {value}
            </p>
            {subtitle && (
              <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
            )}
          </div>
          <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
            <Icon className="w-5 h-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const TradeStatistics: React.FC<TradeStatisticsProps> = ({ trades, loading }) => {
  // Calculate statistics only for closed trades
  const closedTrades = trades.filter(t => t.status === 'closed');
  
  // Basic counts
  const totalTrades = closedTrades.length;
  const winningTrades = closedTrades.filter(t => t.pnl > 0);
  const losingTrades = closedTrades.filter(t => t.pnl < 0);
  const winRate = totalTrades > 0 ? (winningTrades.length / totalTrades) * 100 : 0;
  
  // P&L calculations
  const totalPnL = closedTrades.reduce((sum, t) => sum + t.pnl, 0);
  const avgWin = winningTrades.length > 0 
    ? winningTrades.reduce((sum, t) => sum + t.pnl, 0) / winningTrades.length 
    : 0;
  const avgLoss = losingTrades.length > 0 
    ? Math.abs(losingTrades.reduce((sum, t) => sum + t.pnl, 0) / losingTrades.length)
    : 0;
  
  // Advanced metrics
  const profitFactor = avgLoss > 0 ? avgWin / avgLoss : avgWin > 0 ? Infinity : 0;
  const largestWin = winningTrades.length > 0 
    ? Math.max(...winningTrades.map(t => t.pnl))
    : 0;
  const largestLoss = losingTrades.length > 0 
    ? Math.min(...losingTrades.map(t => t.pnl))
    : 0;
  
  // Calculate current streak
  const calculateStreak = () => {
    if (closedTrades.length === 0) return { type: 'none', count: 0 };
    
    const sortedTrades = [...closedTrades].sort((a, b) => {
      // Assuming trades have some date property or are already in chronological order
      return b.id - a.id;
    });
    
    let streakCount = 0;
    let streakType = sortedTrades[0].pnl > 0 ? 'win' : 'loss';
    
    for (const trade of sortedTrades) {
      if ((streakType === 'win' && trade.pnl > 0) || 
          (streakType === 'loss' && trade.pnl < 0)) {
        streakCount++;
      } else {
        break;
      }
    }
    
    return { type: streakType, count: streakCount };
  };
  
  const streak = calculateStreak();
  
  // Format currency
  const formatCurrency = (amount: number) => {
    const formatted = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(Math.abs(amount));
    
    if (amount >= 0) return `+${formatted}`;
    return `-${formatted}`;
  };
  
  // Loading skeleton
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[...Array(8)].map((_, i) => (
          <Card key={i} padding="sm">
            <CardContent>
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }
  
  return (
    <div className="space-y-4 mb-6">
      {/* Primary Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Trades"
          value={totalTrades}
          icon={Activity}
          color="blue"
          subtitle={`${trades.filter(t => t.status === 'open').length} open`}
        />
        
        <StatCard
          title="Win Rate"
          value={`${winRate.toFixed(1)}%`}
          icon={Target}
          color={winRate >= 50 ? 'green' : 'red'}
          subtitle={`${winningTrades.length}W / ${losingTrades.length}L`}
        />
        
        <StatCard
          title="Total P&L"
          value={formatCurrency(totalPnL)}
          icon={DollarSign}
          color={totalPnL >= 0 ? 'green' : 'red'}
        />
        
        <StatCard
          title="Profit Factor"
          value={profitFactor === Infinity ? '∞' : profitFactor.toFixed(2)}
          icon={TrendingUp}
          color={profitFactor > 1 ? 'green' : 'red'}
          subtitle={profitFactor > 1 ? 'Profitable' : 'Unprofitable'}
        />
      </div>
      
      {/* Secondary Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Average Win"
          value={formatCurrency(avgWin)}
          icon={TrendingUp}
          color="green"
        />
        
        <StatCard
          title="Average Loss"
          value={formatCurrency(avgLoss)}
          icon={TrendingDown}
          color="red"
        />
        
        <StatCard
          title="Largest Win"
          value={formatCurrency(largestWin)}
          icon={Award}
          color="green"
        />
        
        <StatCard
          title="Largest Loss"
          value={formatCurrency(Math.abs(largestLoss))}
          icon={AlertTriangle}
          color="red"
        />
      </div>
      
      {/* Streak Indicator */}
      {streak.count > 0 && (
        <Card padding="sm">
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${
                  streak.type === 'win' 
                    ? 'bg-green-100 text-green-600' 
                    : 'bg-red-100 text-red-600'
                }`}>
                  <Zap className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">Current Streak</p>
                  <p className={`text-lg font-bold ${
                    streak.type === 'win' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {streak.count} {streak.type === 'win' ? 'Wins' : 'Losses'} in a row
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default TradeStatistics;