import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { TrendingUp, TrendingDown, Flame, Snowflake, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface Trade {
  id: number;
  pnl: number;
  exit_date?: string;
  close_date?: string;
  status: 'open' | 'closed';
}

interface StreakIndicatorProps {
  trades: Trade[];
}

interface StreakData {
  current: {
    type: 'win' | 'loss' | 'neutral';
    count: number;
    startDate: Date;
    totalPnL: number;
  };
  history: Array<{
    type: 'win' | 'loss';
    count: number;
    startDate: Date;
    endDate: Date;
    totalPnL: number;
  }>;
  records: {
    longestWinStreak: number;
    longestLossStreak: number;
    bestStreakPnL: number;
    worstStreakPnL: number;
  };
}

const StreakIndicator: React.FC<StreakIndicatorProps> = ({ trades }) => {
  // Calculate streak data
  const streakData = useMemo(() => {
    const closedTrades = trades
      .filter(t => t.status === 'closed')
      .sort((a, b) => {
        const dateA = new Date(a.exit_date || a.close_date || 0);
        const dateB = new Date(b.exit_date || b.close_date || 0);
        return dateA.getTime() - dateB.getTime();
      });
    
    if (closedTrades.length === 0) {
      return {
        current: { type: 'neutral' as const, count: 0, startDate: new Date(), totalPnL: 0 },
        history: [],
        records: {
          longestWinStreak: 0,
          longestLossStreak: 0,
          bestStreakPnL: 0,
          worstStreakPnL: 0
        }
      };
    }
    
    const history: StreakData['history'] = [];
    let currentStreak: StreakData['history'][0] | null = null;
    
    // Process trades to find streaks
    closedTrades.forEach((trade, index) => {
      const isWin = trade.pnl > 0;
      const tradeDate = new Date(trade.exit_date || trade.close_date || 0);
      
      if (!currentStreak) {
        // Start new streak
        currentStreak = {
          type: isWin ? 'win' : 'loss',
          count: 1,
          startDate: tradeDate,
          endDate: tradeDate,
          totalPnL: trade.pnl
        };
      } else if ((currentStreak.type === 'win' && isWin) || 
                 (currentStreak.type === 'loss' && !isWin)) {
        // Continue streak
        currentStreak.count++;
        currentStreak.endDate = tradeDate;
        currentStreak.totalPnL += trade.pnl;
      } else {
        // End streak and start new one
        if (currentStreak.count >= 2) { // Only record streaks of 2 or more
          history.push({ ...currentStreak });
        }
        
        currentStreak = {
          type: isWin ? 'win' : 'loss',
          count: 1,
          startDate: tradeDate,
          endDate: tradeDate,
          totalPnL: trade.pnl
        };
      }
    });
    
    // Add final streak if it qualifies
    if (currentStreak && currentStreak.count >= 2) {
      history.push({ ...currentStreak });
    }
    
    // Calculate current streak (from most recent trades)
    const recentTrades = closedTrades.slice(-10);
    let currentType: 'win' | 'loss' | 'neutral' = 'neutral';
    let currentCount = 0;
    let currentStartIdx = recentTrades.length - 1;
    let currentTotalPnL = 0;
    
    // Work backwards to find current streak
    for (let i = recentTrades.length - 1; i >= 0; i--) {
      const trade = recentTrades[i];
      const isWin = trade.pnl > 0;
      
      if (i === recentTrades.length - 1) {
        currentType = isWin ? 'win' : 'loss';
        currentCount = 1;
        currentTotalPnL = trade.pnl;
      } else if ((currentType === 'win' && isWin) || 
                 (currentType === 'loss' && !isWin)) {
        currentCount++;
        currentStartIdx = i;
        currentTotalPnL += trade.pnl;
      } else {
        break;
      }
    }
    
    // Calculate records
    const winStreaks = history.filter(s => s.type === 'win');
    const lossStreaks = history.filter(s => s.type === 'loss');
    
    const records = {
      longestWinStreak: winStreaks.reduce((max, s) => Math.max(max, s.count), 0),
      longestLossStreak: lossStreaks.reduce((max, s) => Math.max(max, s.count), 0),
      bestStreakPnL: winStreaks.reduce((max, s) => Math.max(max, s.totalPnL), 0),
      worstStreakPnL: lossStreaks.reduce((min, s) => Math.min(min, s.totalPnL), 0)
    };
    
    return {
      current: {
        type: currentType,
        count: currentCount,
        startDate: new Date(recentTrades[currentStartIdx]?.exit_date || 
                           recentTrades[currentStartIdx]?.close_date || 0),
        totalPnL: currentTotalPnL
      },
      history,
      records
    } as StreakData;
  }, [trades]);
  
  // Get streak icon and color
  const getStreakIcon = (type: string, count: number) => {
    if (type === 'win' && count >= 3) return <Flame className="w-6 h-6 text-orange-500" />;
    if (type === 'loss' && count >= 3) return <Snowflake className="w-6 h-6 text-blue-500" />;
    if (type === 'win') return <TrendingUp className="w-6 h-6 text-green-500" />;
    if (type === 'loss') return <TrendingDown className="w-6 h-6 text-red-500" />;
    return <Activity className="w-6 h-6 text-gray-500" />;
  };
  
  const getStreakMessage = (type: string, count: number) => {
    if (type === 'neutral' || count === 0) return 'No active streak';
    
    const streakText = `${count} ${type === 'win' ? 'Win' : 'Loss'}${count !== 1 ? 's' : ''} in a row`;
    
    if (type === 'win' && count >= 5) return `${streakText} 🔥 On Fire!`;
    if (type === 'win' && count >= 3) return `${streakText} 🔥`;
    if (type === 'loss' && count >= 5) return `${streakText} ❄️ Ice Cold!`;
    if (type === 'loss' && count >= 3) return `${streakText} ❄️`;
    
    return streakText;
  };
  
  // Format currency
  const formatCurrency = (amount: number) => {
    const formatted = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(Math.abs(amount));
    return amount >= 0 ? `+${formatted}` : `-${formatted}`;
  };
  
  // Prepare chart data
  const chartData = useMemo(() => {
    return streakData.history
      .slice(-20) // Last 20 streaks
      .map((streak, index) => ({
        index: index + 1,
        count: streak.type === 'win' ? streak.count : -streak.count,
        type: streak.type,
        pnl: streak.totalPnL,
        label: `${streak.count} ${streak.type}s`
      }));
  }, [streakData.history]);
  
  // Calculate streak probability
  const streakProbability = useMemo(() => {
    const totalStreaks = streakData.history.length;
    if (totalStreaks === 0) return { win: 0, loss: 0 };
    
    const winStreaks = streakData.history.filter(s => s.type === 'win').length;
    const lossStreaks = streakData.history.filter(s => s.type === 'loss').length;
    
    return {
      win: (winStreaks / totalStreaks) * 100,
      loss: (lossStreaks / totalStreaks) * 100
    };
  }, [streakData.history]);
  
  return (
    <div className="space-y-6">
      {/* Current Streak */}
      <Card>
        <CardHeader>
          <CardTitle>Current Streak</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {getStreakIcon(streakData.current.type, streakData.current.count)}
              <div>
                <p className="text-xl font-bold">
                  {getStreakMessage(streakData.current.type, streakData.current.count)}
                </p>
                {streakData.current.count > 0 && (
                  <p className={`text-sm ${
                    streakData.current.type === 'win' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(streakData.current.totalPnL)}
                  </p>
                )}
              </div>
            </div>
            
            {/* Streak Probability */}
            <div className="text-right">
              <p className="text-sm text-gray-600">Historical Probability</p>
              <div className="flex items-center space-x-4 mt-1">
                <span className="text-sm">
                  <span className="font-medium text-green-600">{streakProbability.win.toFixed(0)}%</span> Win
                </span>
                <span className="text-sm">
                  <span className="font-medium text-red-600">{streakProbability.loss.toFixed(0)}%</span> Loss
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Streak Records */}
      <Card>
        <CardHeader>
          <CardTitle>Streak Records</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-gray-600">Longest Win Streak</p>
              <p className="text-2xl font-bold text-green-600">
                {streakData.records.longestWinStreak}
              </p>
              <p className="text-xs text-gray-500">consecutive wins</p>
            </div>
            
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <p className="text-sm text-gray-600">Longest Loss Streak</p>
              <p className="text-2xl font-bold text-red-600">
                {streakData.records.longestLossStreak}
              </p>
              <p className="text-xs text-gray-500">consecutive losses</p>
            </div>
            
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-gray-600">Best Streak P&L</p>
              <p className="text-xl font-bold text-green-600">
                {formatCurrency(streakData.records.bestStreakPnL)}
              </p>
            </div>
            
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <p className="text-sm text-gray-600">Worst Streak P&L</p>
              <p className="text-xl font-bold text-red-600">
                {formatCurrency(streakData.records.worstStreakPnL)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Streak History Chart */}
      {chartData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Streak History</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="index" 
                  label={{ value: 'Streak #', position: 'insideBottom', offset: -5 }}
                />
                <YAxis 
                  label={{ value: 'Consecutive Trades', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  content={({ active, payload }) => {
                    if (active && payload && payload[0]) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                          <p className="font-medium">{data.label}</p>
                          <p className={`text-sm ${data.type === 'win' ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(data.pnl)}
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.type === 'win' ? '#10B981' : '#EF4444'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default StreakIndicator;