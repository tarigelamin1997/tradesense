import React, { useMemo, useState } from 'react';
import { 
  eachDayOfInterval, 
  format, 
  startOfMonth, 
  endOfMonth, 
  startOfWeek,
  endOfWeek,
  subMonths,
  isSameMonth,
  isToday,
  getDay
} from 'date-fns';
import { scaleLinear } from 'd3-scale';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { ChevronLeft, ChevronRight, Download } from 'lucide-react';

interface Trade {
  id: number;
  pnl: number;
  exit_date?: string;
  close_date?: string;
  status: 'open' | 'closed';
}

interface PnLHeatmapProps {
  trades: Trade[];
  onDateClick?: (date: Date, trades: Trade[]) => void;
  onExport?: () => void;
}

interface DayData {
  date: Date;
  pnl: number;
  trades: Trade[];
  intensity: number;
}

const PnLHeatmap: React.FC<PnLHeatmapProps> = ({ trades, onDateClick, onExport }) => {
  const [viewDate, setViewDate] = useState(new Date());
  const [hoveredDate, setHoveredDate] = useState<Date | null>(null);
  
  // Color scales
  const colorScale = {
    loss: {
      extreme: '#8B0000',
      high: '#DC143C',
      medium: '#FF6B6B',
      low: '#FFB6C1'
    },
    profit: {
      low: '#90EE90',
      medium: '#32CD32',
      high: '#228B22',
      extreme: '#006400'
    },
    neutral: '#E0E0E0',
    empty: '#F5F5F5'
  };
  
  // Process trades into daily P&L
  const dailyData = useMemo(() => {
    const dataMap = new Map<string, DayData>();
    
    // Initialize 12 months of dates
    const endDate = endOfMonth(viewDate);
    const startDate = startOfMonth(subMonths(viewDate, 11));
    const allDays = eachDayOfInterval({ start: startDate, end: endDate });
    
    // Initialize all days
    allDays.forEach(date => {
      const key = format(date, 'yyyy-MM-dd');
      dataMap.set(key, {
        date,
        pnl: 0,
        trades: [],
        intensity: 0
      });
    });
    
    // Aggregate trades by day
    trades.forEach(trade => {
      if (trade.status === 'closed' && (trade.exit_date || trade.close_date)) {
        const dateStr = trade.exit_date || trade.close_date || '';
        const key = dateStr.split('T')[0]; // Extract date part
        
        const existing = dataMap.get(key);
        if (existing) {
          existing.pnl += trade.pnl;
          existing.trades.push(trade);
        }
      }
    });
    
    // Calculate intensity levels
    const pnlValues = Array.from(dataMap.values())
      .map(d => d.pnl)
      .filter(pnl => pnl !== 0);
    
    if (pnlValues.length > 0) {
      const maxProfit = Math.max(...pnlValues.filter(v => v > 0), 0);
      const maxLoss = Math.abs(Math.min(...pnlValues.filter(v => v < 0), 0));
      
      const profitScale = scaleLinear()
        .domain([0, maxProfit * 0.25, maxProfit * 0.5, maxProfit * 0.75, maxProfit])
        .range([0, 1, 2, 3, 4]);
        
      const lossScale = scaleLinear()
        .domain([0, maxLoss * 0.25, maxLoss * 0.5, maxLoss * 0.75, maxLoss])
        .range([0, -1, -2, -3, -4]);
      
      dataMap.forEach(dayData => {
        if (dayData.pnl > 0) {
          dayData.intensity = Math.round(profitScale(dayData.pnl));
        } else if (dayData.pnl < 0) {
          dayData.intensity = Math.round(lossScale(Math.abs(dayData.pnl)));
        }
      });
    }
    
    return dataMap;
  }, [trades, viewDate]);
  
  // Get color for a day based on P&L
  const getDayColor = (dayData: DayData) => {
    if (dayData.trades.length === 0) return colorScale.empty;
    if (dayData.pnl === 0) return colorScale.neutral;
    
    if (dayData.pnl > 0) {
      switch (dayData.intensity) {
        case 4: return colorScale.profit.extreme;
        case 3: return colorScale.profit.high;
        case 2: return colorScale.profit.medium;
        case 1: return colorScale.profit.low;
        default: return colorScale.neutral;
      }
    } else {
      switch (Math.abs(dayData.intensity)) {
        case 4: return colorScale.loss.extreme;
        case 3: return colorScale.loss.high;
        case 2: return colorScale.loss.medium;
        case 1: return colorScale.loss.low;
        default: return colorScale.neutral;
      }
    }
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
  
  // Render calendar grid
  const renderCalendar = () => {
    const months = [];
    
    for (let i = 11; i >= 0; i--) {
      const monthDate = subMonths(viewDate, i);
      const monthStart = startOfMonth(monthDate);
      const monthEnd = endOfMonth(monthDate);
      const calendarStart = startOfWeek(monthStart);
      const calendarEnd = endOfWeek(monthEnd);
      
      const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd });
      
      months.push(
        <div key={format(monthDate, 'yyyy-MM')} className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            {format(monthDate, 'MMMM yyyy')}
          </h4>
          <div className="grid grid-cols-7 gap-1">
            {/* Day headers */}
            {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, idx) => (
              <div key={idx} className="text-xs text-gray-500 text-center p-1">
                {day}
              </div>
            ))}
            
            {/* Calendar days */}
            {days.map((date) => {
              const key = format(date, 'yyyy-MM-dd');
              const dayData = dailyData.get(key) || { 
                date, 
                pnl: 0, 
                trades: [], 
                intensity: 0 
              };
              const isCurrentMonth = isSameMonth(date, monthDate);
              const isHovered = hoveredDate && format(hoveredDate, 'yyyy-MM-dd') === key;
              
              return (
                <div
                  key={key}
                  className={`
                    relative aspect-square rounded cursor-pointer transition-all
                    ${isCurrentMonth ? 'opacity-100' : 'opacity-30'}
                    ${isToday(date) ? 'ring-2 ring-blue-500' : ''}
                    ${isHovered ? 'ring-2 ring-gray-600 z-10' : ''}
                  `}
                  style={{ backgroundColor: getDayColor(dayData) }}
                  onMouseEnter={() => setHoveredDate(date)}
                  onMouseLeave={() => setHoveredDate(null)}
                  onClick={() => onDateClick && onDateClick(date, dayData.trades)}
                >
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xs text-gray-700">
                      {format(date, 'd')}
                    </span>
                  </div>
                  
                  {/* Tooltip */}
                  {isHovered && dayData.trades.length > 0 && (
                    <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 z-20">
                      <div className="bg-gray-900 text-white text-xs rounded px-3 py-2 whitespace-nowrap">
                        <div className="font-medium">{format(date, 'MMM d, yyyy')}</div>
                        <div className={dayData.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                          {formatCurrency(dayData.pnl)}
                        </div>
                        <div className="text-gray-400">
                          {dayData.trades.length} trade{dayData.trades.length !== 1 ? 's' : ''}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      );
    }
    
    return months;
  };
  
  // Calculate summary stats
  const summaryStats = useMemo(() => {
    const allDays = Array.from(dailyData.values());
    const tradingDays = allDays.filter(d => d.trades.length > 0);
    const profitDays = tradingDays.filter(d => d.pnl > 0);
    const lossDays = tradingDays.filter(d => d.pnl < 0);
    
    return {
      totalDays: tradingDays.length,
      profitDays: profitDays.length,
      lossDays: lossDays.length,
      bestDay: tradingDays.reduce((best, day) => 
        day.pnl > best.pnl ? day : best, 
        { pnl: -Infinity, date: new Date() }
      ),
      worstDay: tradingDays.reduce((worst, day) => 
        day.pnl < worst.pnl ? day : worst, 
        { pnl: Infinity, date: new Date() }
      )
    };
  }, [dailyData]);
  
  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>P&L Calendar</CardTitle>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewDate(subMonths(viewDate, 1))}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewDate(new Date())}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
            >
              Today
            </button>
            <button
              onClick={() => setViewDate(d => new Date(Math.min(d.getTime() + 2592000000, Date.now())))}
              disabled={viewDate.getTime() >= Date.now()}
              className="p-1 hover:bg-gray-100 rounded disabled:opacity-50"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
            {onExport && (
              <button
                onClick={onExport}
                className="p-1 hover:bg-gray-100 rounded"
                title="Export calendar"
              >
                <Download className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Legend */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-600">Loss</span>
              <div className="flex space-x-1">
                {Object.values(colorScale.loss).reverse().map((color, idx) => (
                  <div
                    key={idx}
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>
            <div className="w-4 h-4 rounded" style={{ backgroundColor: colorScale.neutral }} />
            <div className="flex items-center space-x-2">
              <div className="flex space-x-1">
                {Object.values(colorScale.profit).map((color, idx) => (
                  <div
                    key={idx}
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
              <span className="text-xs text-gray-600">Profit</span>
            </div>
          </div>
          
          {/* Summary Stats */}
          <div className="flex items-center space-x-6 text-xs text-gray-600">
            <div>
              <span className="font-medium">{summaryStats.totalDays}</span> trading days
            </div>
            <div>
              <span className="font-medium text-green-600">{summaryStats.profitDays}</span> profit
            </div>
            <div>
              <span className="font-medium text-red-600">{summaryStats.lossDays}</span> loss
            </div>
          </div>
        </div>
        
        {/* Calendar Grid */}
        <div className="overflow-x-auto">
          <div className="min-w-[600px]">
            {renderCalendar()}
          </div>
        </div>
        
        {/* Best/Worst Day */}
        {summaryStats.totalDays > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-200 grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Best Day</p>
              <p className="text-lg font-semibold text-green-600">
                {formatCurrency(summaryStats.bestDay.pnl)}
              </p>
              <p className="text-xs text-gray-500">
                {format(summaryStats.bestDay.date, 'MMM d, yyyy')}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Worst Day</p>
              <p className="text-lg font-semibold text-red-600">
                {formatCurrency(summaryStats.worstDay.pnl)}
              </p>
              <p className="text-xs text-gray-500">
                {format(summaryStats.worstDay.date, 'MMM d, yyyy')}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default PnLHeatmap;