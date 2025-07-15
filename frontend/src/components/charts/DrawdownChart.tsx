import React, { useMemo } from 'react';
import { 
  AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea 
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { AlertTriangle, TrendingDown, Clock, CheckCircle } from 'lucide-react';
import { format, differenceInDays } from 'date-fns';

interface Trade {
  id: number;
  pnl: number;
  exit_date?: string;
  close_date?: string;
  status: 'open' | 'closed';
}

interface DrawdownChartProps {
  trades: Trade[];
}

interface DrawdownPoint {
  date: string;
  equity: number;
  peak: number;
  drawdown: number;
  drawdownPercent: number;
  inDrawdown: boolean;
}

interface DrawdownPeriod {
  startDate: string;
  endDate: string | null;
  startValue: number;
  bottomValue: number;
  endValue: number | null;
  maxDrawdown: number;
  maxDrawdownPercent: number;
  duration: number | null;
  recovered: boolean;
}

const DrawdownChart: React.FC<DrawdownChartProps> = ({ trades }) => {
  // Calculate drawdown series
  const { drawdownSeries, drawdownPeriods, stats } = useMemo(() => {
    const closedTrades = trades
      .filter(t => t.status === 'closed')
      .sort((a, b) => {
        const dateA = new Date(a.exit_date || a.close_date || 0);
        const dateB = new Date(b.exit_date || b.close_date || 0);
        return dateA.getTime() - dateB.getTime();
      });
    
    if (closedTrades.length === 0) {
      return {
        drawdownSeries: [],
        drawdownPeriods: [],
        stats: {
          currentDrawdown: 0,
          currentDrawdownPercent: 0,
          maxDrawdown: 0,
          maxDrawdownPercent: 0,
          avgDrawdown: 0,
          avgDrawdownPercent: 0,
          timeInDrawdown: 0,
          avgRecoveryTime: 0,
          numberOfDrawdowns: 0
        }
      };
    }
    
    let equity = 0;
    let peak = 0;
    const series: DrawdownPoint[] = [];
    const periods: DrawdownPeriod[] = [];
    let currentPeriod: DrawdownPeriod | null = null;
    
    // Calculate drawdown series
    closedTrades.forEach((trade) => {
      equity += trade.pnl;
      const date = trade.exit_date || trade.close_date || '';
      
      if (equity > peak) {
        // New peak reached
        if (currentPeriod && !currentPeriod.recovered) {
          // End current drawdown period
          currentPeriod.endDate = date;
          currentPeriod.endValue = equity;
          currentPeriod.recovered = true;
          currentPeriod.duration = differenceInDays(
            new Date(currentPeriod.endDate),
            new Date(currentPeriod.startDate)
          );
          periods.push({ ...currentPeriod });
          currentPeriod = null;
        }
        peak = equity;
      }
      
      const drawdown = peak > 0 ? equity - peak : 0;
      const drawdownPercent = peak > 0 ? (drawdown / peak) * 100 : 0;
      const inDrawdown = drawdown < 0;
      
      // Start new drawdown period if needed
      if (inDrawdown && !currentPeriod) {
        currentPeriod = {
          startDate: date,
          endDate: null,
          startValue: peak,
          bottomValue: equity,
          endValue: null,
          maxDrawdown: drawdown,
          maxDrawdownPercent: drawdownPercent,
          duration: null,
          recovered: false
        };
      } else if (inDrawdown && currentPeriod) {
        // Update current drawdown period
        if (equity < currentPeriod.bottomValue) {
          currentPeriod.bottomValue = equity;
          currentPeriod.maxDrawdown = equity - currentPeriod.startValue;
          currentPeriod.maxDrawdownPercent = 
            (currentPeriod.maxDrawdown / currentPeriod.startValue) * 100;
        }
      }
      
      series.push({
        date,
        equity,
        peak,
        drawdown,
        drawdownPercent,
        inDrawdown
      });
    });
    
    // Add unrecovered drawdown period if exists
    if (currentPeriod && !currentPeriod.recovered) {
      currentPeriod.duration = differenceInDays(
        new Date(series[series.length - 1].date),
        new Date(currentPeriod.startDate)
      );
      periods.push(currentPeriod);
    }
    
    // Calculate statistics
    const drawdowns = series.filter(p => p.drawdown < 0);
    const maxDrawdownPoint = series.reduce((max, p) => 
      p.drawdown < max.drawdown ? p : max,
      { drawdown: 0, drawdownPercent: 0 }
    );
    
    const recoveredPeriods = periods.filter(p => p.recovered);
    const avgRecoveryTime = recoveredPeriods.length > 0
      ? recoveredPeriods.reduce((sum, p) => sum + (p.duration || 0), 0) / recoveredPeriods.length
      : 0;
    
    const stats = {
      currentDrawdown: series.length > 0 ? series[series.length - 1].drawdown : 0,
      currentDrawdownPercent: series.length > 0 ? series[series.length - 1].drawdownPercent : 0,
      maxDrawdown: maxDrawdownPoint.drawdown,
      maxDrawdownPercent: maxDrawdownPoint.drawdownPercent,
      avgDrawdown: drawdowns.length > 0
        ? drawdowns.reduce((sum, p) => sum + p.drawdown, 0) / drawdowns.length
        : 0,
      avgDrawdownPercent: drawdowns.length > 0
        ? drawdowns.reduce((sum, p) => sum + p.drawdownPercent, 0) / drawdowns.length
        : 0,
      timeInDrawdown: (drawdowns.length / series.length) * 100,
      avgRecoveryTime,
      numberOfDrawdowns: periods.length
    };
    
    return { drawdownSeries: series, drawdownPeriods: periods, stats };
  }, [trades]);
  
  // Drawdown zones for coloring
  const getDrawdownColor = (percent: number) => {
    const absPercent = Math.abs(percent);
    if (absPercent < 5) return '#90EE90';     // Green - Safe
    if (absPercent < 10) return '#FFD700';    // Yellow - Caution
    if (absPercent < 20) return '#FF8C00';    // Orange - Warning
    return '#DC143C';                         // Red - Danger
  };
  
  // Format currency
  const formatCurrency = (amount: number) => {
    const formatted = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(Math.abs(amount));
    return amount >= 0 ? formatted : `-${formatted}`;
  };
  
  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload[0]) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="text-sm text-gray-600">
            {format(new Date(data.date), 'MMM dd, yyyy')}
          </p>
          <p className="text-sm">
            Equity: <span className="font-medium">{formatCurrency(data.equity)}</span>
          </p>
          <p className="text-sm">
            Peak: <span className="font-medium">{formatCurrency(data.peak)}</span>
          </p>
          {data.inDrawdown && (
            <>
              <p className="text-sm text-red-600">
                Drawdown: <span className="font-medium">{formatCurrency(data.drawdown)}</span>
              </p>
              <p className="text-sm text-red-600">
                {data.drawdownPercent.toFixed(2)}% from peak
              </p>
            </>
          )}
        </div>
      );
    }
    return null;
  };
  
  return (
    <div className="space-y-6">
      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Current Drawdown</p>
              <p className={`text-xl font-bold ${
                stats.currentDrawdown < 0 ? 'text-red-600' : 'text-green-600'
              }`}>
                {stats.currentDrawdownPercent.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500">
                {formatCurrency(stats.currentDrawdown)}
              </p>
            </div>
            <TrendingDown className={`w-5 h-5 ${
              stats.currentDrawdown < 0 ? 'text-red-500' : 'text-gray-400'
            }`} />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Max Drawdown</p>
              <p className="text-xl font-bold text-red-600">
                {stats.maxDrawdownPercent.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500">
                {formatCurrency(stats.maxDrawdown)}
              </p>
            </div>
            <AlertTriangle className="w-5 h-5 text-red-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Time in Drawdown</p>
              <p className="text-xl font-bold">
                {stats.timeInDrawdown.toFixed(0)}%
              </p>
              <p className="text-xs text-gray-500">
                {stats.numberOfDrawdowns} periods
              </p>
            </div>
            <Clock className="w-5 h-5 text-blue-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Recovery</p>
              <p className="text-xl font-bold">
                {stats.avgRecoveryTime.toFixed(0)}d
              </p>
              <p className="text-xs text-gray-500">
                days to recover
              </p>
            </div>
            <CheckCircle className="w-5 h-5 text-green-500" />
          </div>
        </Card>
      </div>
      
      {/* Underwater Equity Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Underwater Equity Curve</CardTitle>
        </CardHeader>
        <CardContent>
          {drawdownSeries.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart 
                data={drawdownSeries}
                margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#DC143C" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#DC143C" stopOpacity={0.2}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date"
                  tickFormatter={(date) => format(new Date(date), 'MMM dd')}
                />
                <YAxis 
                  tickFormatter={(value) => `${value.toFixed(0)}%`}
                />
                <Tooltip content={<CustomTooltip />} />
                
                {/* Reference lines for zones */}
                <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" />
                <ReferenceLine y={-5} stroke="#90EE90" strokeDasharray="2 2" />
                <ReferenceLine y={-10} stroke="#FFD700" strokeDasharray="2 2" />
                <ReferenceLine y={-20} stroke="#FF8C00" strokeDasharray="2 2" />
                
                {/* Drawdown periods */}
                {drawdownPeriods.map((period, index) => (
                  <ReferenceArea
                    key={index}
                    x1={period.startDate}
                    x2={period.endDate || drawdownSeries[drawdownSeries.length - 1].date}
                    fill={period.recovered ? '#10B981' : '#DC143C'}
                    fillOpacity={0.1}
                  />
                ))}
                
                <Area
                  type="monotone"
                  dataKey="drawdownPercent"
                  stroke="#DC143C"
                  fill="url(#drawdownGradient)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[400px] text-gray-500">
              No drawdown data available
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Drawdown Periods Table */}
      {drawdownPeriods.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Drawdown Periods</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Period
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Max Drawdown
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Duration
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {drawdownPeriods.slice(-10).reverse().map((period, index) => (
                    <tr key={index}>
                      <td className="px-4 py-2 text-sm">
                        {format(new Date(period.startDate), 'MMM dd, yyyy')} - 
                        {period.endDate 
                          ? format(new Date(period.endDate), 'MMM dd, yyyy')
                          : 'Present'
                        }
                      </td>
                      <td className="px-4 py-2 text-sm">
                        <span className="text-red-600 font-medium">
                          {period.maxDrawdownPercent.toFixed(1)}%
                        </span>
                        <span className="text-gray-500 text-xs ml-1">
                          ({formatCurrency(period.maxDrawdown)})
                        </span>
                      </td>
                      <td className="px-4 py-2 text-sm">
                        {period.duration} days
                      </td>
                      <td className="px-4 py-2 text-sm">
                        {period.recovered ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Recovered
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                            <AlertTriangle className="w-3 h-3 mr-1" />
                            Active
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DrawdownChart;