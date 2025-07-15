import { 
  startOfMonth, 
  endOfMonth, 
  eachDayOfInterval, 
  format,
  differenceInDays 
} from 'date-fns';

interface Trade {
  id: number;
  pnl: number;
  exit_date?: string;
  close_date?: string;
  entry_date?: string;
  open_date?: string;
  status: 'open' | 'closed';
}

// Calculate daily P&L aggregates
export const calculateDailyPnL = (trades: Trade[]) => {
  const dailyMap = new Map<string, number>();
  
  trades
    .filter(t => t.status === 'closed')
    .forEach(trade => {
      const date = trade.exit_date || trade.close_date || '';
      const dateKey = date.split('T')[0];
      
      if (dateKey) {
        const existing = dailyMap.get(dateKey) || 0;
        dailyMap.set(dateKey, existing + trade.pnl);
      }
    });
  
  return Array.from(dailyMap.entries())
    .map(([date, pnl]) => ({ date, pnl }))
    .sort((a, b) => a.date.localeCompare(b.date));
};

// Calculate cumulative P&L
export const calculateCumulativePnL = (trades: Trade[]) => {
  const sorted = trades
    .filter(t => t.status === 'closed')
    .sort((a, b) => {
      const dateA = new Date(a.exit_date || a.close_date || 0);
      const dateB = new Date(b.exit_date || b.close_date || 0);
      return dateA.getTime() - dateB.getTime();
    });
  
  let cumulative = 0;
  return sorted.map(trade => {
    cumulative += trade.pnl;
    return {
      date: trade.exit_date || trade.close_date || '',
      value: cumulative,
      trade
    };
  });
};

// Calculate win rate over time
export const calculateWinRateOverTime = (trades: Trade[], windowSize: number = 20) => {
  const sorted = trades
    .filter(t => t.status === 'closed')
    .sort((a, b) => {
      const dateA = new Date(a.exit_date || a.close_date || 0);
      const dateB = new Date(b.exit_date || b.close_date || 0);
      return dateA.getTime() - dateB.getTime();
    });
  
  return sorted.map((trade, index) => {
    const windowStart = Math.max(0, index - windowSize + 1);
    const window = sorted.slice(windowStart, index + 1);
    const wins = window.filter(t => t.pnl > 0).length;
    const winRate = (wins / window.length) * 100;
    
    return {
      date: trade.exit_date || trade.close_date || '',
      winRate,
      trades: window.length
    };
  });
};

// Calculate monthly statistics
export const calculateMonthlyStats = (trades: Trade[]) => {
  const monthlyMap = new Map<string, { pnl: number; count: number; wins: number }>();
  
  trades
    .filter(t => t.status === 'closed')
    .forEach(trade => {
      const date = new Date(trade.exit_date || trade.close_date || 0);
      const monthKey = format(date, 'yyyy-MM');
      
      const existing = monthlyMap.get(monthKey) || { pnl: 0, count: 0, wins: 0 };
      monthlyMap.set(monthKey, {
        pnl: existing.pnl + trade.pnl,
        count: existing.count + 1,
        wins: existing.wins + (trade.pnl > 0 ? 1 : 0)
      });
    });
  
  return Array.from(monthlyMap.entries())
    .map(([month, stats]) => ({
      month,
      pnl: stats.pnl,
      trades: stats.count,
      winRate: (stats.wins / stats.count) * 100
    }))
    .sort((a, b) => a.month.localeCompare(b.month));
};

// Calculate time-based statistics
export const calculateTimeStats = (trades: Trade[]) => {
  const hourlyStats = new Array(24).fill(0).map(() => ({ wins: 0, losses: 0, pnl: 0 }));
  const dailyStats = new Array(7).fill(0).map(() => ({ wins: 0, losses: 0, pnl: 0 }));
  
  trades
    .filter(t => t.status === 'closed')
    .forEach(trade => {
      const date = new Date(trade.exit_date || trade.close_date || 0);
      const hour = date.getHours();
      const day = date.getDay();
      
      if (trade.pnl > 0) {
        hourlyStats[hour].wins++;
        dailyStats[day].wins++;
      } else {
        hourlyStats[hour].losses++;
        dailyStats[day].losses++;
      }
      
      hourlyStats[hour].pnl += trade.pnl;
      dailyStats[day].pnl += trade.pnl;
    });
  
  return { hourlyStats, dailyStats };
};

// Calculate performance metrics
export const calculatePerformanceMetrics = (trades: Trade[]) => {
  const closedTrades = trades.filter(t => t.status === 'closed');
  
  if (closedTrades.length === 0) {
    return {
      totalPnL: 0,
      winRate: 0,
      profitFactor: 0,
      sharpeRatio: 0,
      maxDrawdown: 0,
      avgWin: 0,
      avgLoss: 0,
      expectancy: 0
    };
  }
  
  const winners = closedTrades.filter(t => t.pnl > 0);
  const losers = closedTrades.filter(t => t.pnl < 0);
  
  const totalWins = winners.reduce((sum, t) => sum + t.pnl, 0);
  const totalLosses = Math.abs(losers.reduce((sum, t) => sum + t.pnl, 0));
  
  const avgWin = winners.length > 0 ? totalWins / winners.length : 0;
  const avgLoss = losers.length > 0 ? totalLosses / losers.length : 0;
  
  const winRate = (winners.length / closedTrades.length) * 100;
  const profitFactor = totalLosses > 0 ? totalWins / totalLosses : totalWins > 0 ? Infinity : 0;
  
  // Calculate expectancy
  const winProb = winners.length / closedTrades.length;
  const lossProb = losers.length / closedTrades.length;
  const expectancy = (winProb * avgWin) - (lossProb * avgLoss);
  
  // Calculate Sharpe Ratio (simplified)
  const returns = closedTrades.map(t => t.pnl);
  const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
  const stdDev = Math.sqrt(
    returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length
  );
  const sharpeRatio = stdDev > 0 ? (avgReturn / stdDev) * Math.sqrt(252) : 0; // Annualized
  
  // Calculate max drawdown
  let peak = 0;
  let maxDrawdown = 0;
  let cumulative = 0;
  
  closedTrades.forEach(trade => {
    cumulative += trade.pnl;
    peak = Math.max(peak, cumulative);
    const drawdown = peak > 0 ? ((cumulative - peak) / peak) * 100 : 0;
    maxDrawdown = Math.min(maxDrawdown, drawdown);
  });
  
  return {
    totalPnL: closedTrades.reduce((sum, t) => sum + t.pnl, 0),
    winRate,
    profitFactor,
    sharpeRatio,
    maxDrawdown: Math.abs(maxDrawdown),
    avgWin,
    avgLoss,
    expectancy
  };
};

// Generate test data for charts
export const generateTestData = (days: number = 365) => {
  const trades: Trade[] = [];
  let id = 1;
  let currentDate = new Date();
  currentDate.setDate(currentDate.getDate() - days);
  
  for (let i = 0; i < days * 2; i++) { // Average 2 trades per day
    const isWin = Math.random() > 0.45; // 55% win rate
    const pnl = isWin 
      ? Math.random() * 500 + 50  // Wins: $50-$550
      : -(Math.random() * 400 + 50); // Losses: $50-$450
    
    currentDate.setHours(currentDate.getHours() + Math.random() * 12);
    
    trades.push({
      id: id++,
      pnl,
      exit_date: currentDate.toISOString(),
      close_date: currentDate.toISOString(),
      status: 'closed'
    });
  }
  
  return trades;
};