
import React, { useState, useEffect } from 'react';
import { DailyTimelineData } from '../../../services/timeline';

interface TimelineHeatmapProps {
  timelineData: Record<string, DailyTimelineData>;
  onDateClick: (date: string, dayData: DailyTimelineData) => void;
  startDate: string;
  endDate: string;
}

export const TimelineHeatmap: React.FC<TimelineHeatmapProps> = ({
  timelineData,
  onDateClick,
  startDate,
  endDate
}) => {
  const [weeks, setWeeks] = useState<DailyTimelineData[][]>([]);

  useEffect(() => {
    generateWeeks();
  }, [timelineData, startDate, endDate]);

  const generateWeeks = () => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const weeks: DailyTimelineData[][] = [];
    let currentWeek: DailyTimelineData[] = [];

    // Start from the first day of the week containing start date
    const firstDay = new Date(start);
    firstDay.setDate(start.getDate() - start.getDay());

    let currentDate = new Date(firstDay);

    while (currentDate <= end || currentWeek.length > 0) {
      if (currentWeek.length === 7) {
        weeks.push([...currentWeek]);
        currentWeek = [];
      }

      const dateStr = currentDate.toISOString().split('T')[0];
      const dayData = timelineData[dateStr];

      if (dayData) {
        currentWeek.push(dayData);
      } else {
        // Create empty day data for dates outside range
        currentWeek.push({
          date: dateStr,
          pnl: 0,
          trade_count: 0,
          trades: []
        });
      }

      currentDate.setDate(currentDate.getDate() + 1);

      // Break if we've gone past the end date and completed the week
      if (currentDate > end && currentWeek.length === 7) {
        weeks.push([...currentWeek]);
        break;
      }
    }

    setWeeks(weeks);
  };

  const getPnlColor = (pnl: number, tradeCount: number) => {
    if (tradeCount === 0) return 'bg-gray-100';
    
    const intensity = Math.min(Math.abs(pnl) / 500, 1); // Normalize to 0-1
    
    if (pnl > 0) {
      // Green shades for profit
      if (intensity > 0.8) return 'bg-green-600';
      if (intensity > 0.6) return 'bg-green-500';
      if (intensity > 0.4) return 'bg-green-400';
      if (intensity > 0.2) return 'bg-green-300';
      return 'bg-green-200';
    } else if (pnl < 0) {
      // Red shades for loss
      if (intensity > 0.8) return 'bg-red-600';
      if (intensity > 0.6) return 'bg-red-500';
      if (intensity > 0.4) return 'bg-red-400';
      if (intensity > 0.2) return 'bg-red-300';
      return 'bg-red-200';
    }
    
    return 'bg-gray-200';
  };

  const formatPnl = (pnl: number) => {
    if (pnl === 0) return '$0';
    return `${pnl > 0 ? '+' : ''}$${pnl.toFixed(0)}`;
  };

  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="timeline-heatmap">
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Trading Timeline</h3>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <span>Less</span>
            <div className="flex gap-1">
              <div className="w-3 h-3 bg-gray-100 rounded-sm"></div>
              <div className="w-3 h-3 bg-green-200 rounded-sm"></div>
              <div className="w-3 h-3 bg-green-400 rounded-sm"></div>
              <div className="w-3 h-3 bg-green-600 rounded-sm"></div>
            </div>
            <span>More Profit</span>
          </div>
          <div className="flex items-center gap-2 ml-4">
            <span>More Loss</span>
            <div className="flex gap-1">
              <div className="w-3 h-3 bg-red-600 rounded-sm"></div>
              <div className="w-3 h-3 bg-red-400 rounded-sm"></div>
              <div className="w-3 h-3 bg-red-200 rounded-sm"></div>
            </div>
            <span>Less</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-8 gap-1">
        {/* Day labels */}
        <div></div>
        {weekDays.map(day => (
          <div key={day} className="text-xs text-gray-500 text-center py-1">
            {day}
          </div>
        ))}

        {/* Calendar grid */}
        {weeks.map((week, weekIndex) => (
          <React.Fragment key={weekIndex}>
            <div className="text-xs text-gray-500 py-1 pr-2">
              {weekIndex === 0 && new Date(week[0].date).toLocaleDateString('en-US', { month: 'short' })}
            </div>
            {week.map((day, dayIndex) => (
              <div
                key={`${weekIndex}-${dayIndex}`}
                className={`
                  w-4 h-4 rounded-sm cursor-pointer relative group transition-all duration-200 hover:scale-110
                  ${getPnlColor(day.pnl, day.trade_count)}
                `}
                onClick={() => onDateClick(day.date, day)}
              >
                {/* Emoji overlay */}
                {day.emotion_emoji && (
                  <div className="absolute -top-1 -right-1 text-xs">
                    {day.emotion_emoji}
                  </div>
                )}

                {/* Tooltip */}
                <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-black text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity z-10 whitespace-nowrap">
                  <div>{new Date(day.date).toLocaleDateString()}</div>
                  <div>{formatPnl(day.pnl)}</div>
                  <div>{day.trade_count} trades</div>
                  {day.dominant_emotion && (
                    <div className="capitalize">{day.dominant_emotion}</div>
                  )}
                </div>
              </div>
            ))}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};
