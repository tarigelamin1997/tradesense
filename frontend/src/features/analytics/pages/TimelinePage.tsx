
import React, { useState, useEffect } from 'react';
import { TimelineHeatmap } from '../components/TimelineHeatmap';
import { DailyDiaryModal } from '../components/DailyDiaryModal';
import { timelineService, TimelineResponse, DailyTimelineData } from '../../../services/timeline';

export const TimelinePage: React.FC = () => {
  const [timelineData, setTimelineData] = useState<TimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDay, setSelectedDay] = useState<DailyTimelineData | null>(null);
  const [showDiary, setShowDiary] = useState(false);
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 90 days ago
    end: new Date().toISOString().split('T')[0] // today
  });

  useEffect(() => {
    loadTimelineData();
  }, [dateRange]);

  const loadTimelineData = async () => {
    try {
      setLoading(true);
      const data = await timelineService.getTimeline(dateRange.start, dateRange.end);
      setTimelineData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load timeline data');
    } finally {
      setLoading(false);
    }
  };

  const handleDateClick = (date: string, dayData: DailyTimelineData) => {
    setSelectedDay(dayData);
    setShowDiary(true);
  };

  const handleModalClose = () => {
    setShowDiary(false);
    setSelectedDay(null);
    // Refresh data to show updated reflections
    loadTimelineData();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-800">Error loading timeline: {error}</p>
        <button 
          onClick={loadTimelineData}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!timelineData) return null;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Trading Timeline</h1>
          <p className="text-gray-600 mt-1">
            Visual memory of your trading journey and emotional patterns
          </p>
        </div>
        
        {/* Date Range Selector */}
        <div className="flex gap-4 items-center">
          <div>
            <label className="block text-sm text-gray-600">From</label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
              className="border rounded px-3 py-1"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600">To</label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
              className="border rounded px-3 py-1"
            />
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Total Days</div>
          <div className="text-2xl font-bold">{timelineData.total_days}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Trading Days</div>
          <div className="text-2xl font-bold text-blue-600">{timelineData.trading_days}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Best Day</div>
          <div className="text-lg font-bold text-green-600">
            {timelineData.best_day ? formatCurrency(timelineData.best_day.pnl) : 'N/A'}
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Worst Day</div>
          <div className="text-lg font-bold text-red-600">
            {timelineData.worst_day ? formatCurrency(timelineData.worst_day.pnl) : 'N/A'}
          </div>
        </div>
      </div>

      {/* Timeline Heatmap */}
      <div className="bg-white p-6 rounded-lg shadow">
        <TimelineHeatmap
          timelineData={timelineData.timeline_data}
          onDateClick={handleDateClick}
          startDate={timelineData.date_range.start_date}
          endDate={timelineData.date_range.end_date}
        />
      </div>

      {/* Emotional Patterns Summary */}
      {timelineData.emotional_patterns.most_common_emotion && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Emotional Patterns</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-2">Most Common Emotion</h4>
              <div className="text-lg capitalize">
                {timelineData.emotional_patterns.most_common_emotion}
              </div>
            </div>
            <div>
              <h4 className="font-medium mb-2">Best Trading Day</h4>
              <div className="text-lg">
                {timelineData.emotional_patterns.best_weekday || 'N/A'}
              </div>
            </div>
          </div>
          
          {/* Weekday Performance */}
          {Object.keys(timelineData.emotional_patterns.weekday_performance).length > 0 && (
            <div className="mt-4">
              <h4 className="font-medium mb-2">Performance by Day of Week</h4>
              <div className="grid grid-cols-7 gap-2">
                {Object.entries(timelineData.emotional_patterns.weekday_performance).map(([day, pnl]) => (
                  <div key={day} className="text-center">
                    <div className="text-sm text-gray-600">{day.slice(0, 3)}</div>
                    <div className={`text-sm font-medium ${pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(pnl)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Daily Diary Modal */}
      {showDiary && selectedDay && (
        <DailyDiaryModal
          isOpen={showDiary}
          onClose={handleModalClose}
          dayData={selectedDay}
        />
      )}
    </div>
  );
};
