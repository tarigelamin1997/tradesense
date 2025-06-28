import React, { useState, useMemo } from 'react';
import { Calendar, TrendingUp, TrendingDown, Minus, Filter, Search, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface JournalEntry {
  id: string;
  date: string;
  title: string;
  content: string;
  mood?: 'excellent' | 'good' | 'neutral' | 'poor' | 'terrible';
  confidence?: number;
  trades?: {
    symbol: string;
    pnl: number;
    direction: 'long' | 'short';
  }[];
  tags: string[];
  reflections?: {
    whatWorked: string;
    whatDidnt: string;
    lessons: string;
  };
  marketContext?: {
    regime: string;
    volatility: 'high' | 'medium' | 'low';
    sentiment: string;
  };
}

interface JournalTimelineProps {
  entries: JournalEntry[];
  onEntryClick?: (entry: JournalEntry) => void;
  className?: string;
}

export const JournalTimeline: React.FC<JournalTimelineProps> = ({
  entries,
  onEntryClick,
  className = ""
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterMood, setFilterMood] = useState<string>('all');
  const [filterDateRange, setFilterDateRange] = useState<'week' | 'month' | 'quarter' | 'all'>('all');
  const [showFilters, setShowFilters] = useState(false);

  // Filter entries based on search and filters
  const filteredEntries = useMemo(() => {
    let filtered = entries.filter(entry => {
      const matchesSearch = entry.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           entry.content.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesMood = filterMood === 'all' || entry.mood === filterMood;

      let matchesDate = true;
      if (filterDateRange !== 'all') {
        const entryDate = new Date(entry.date);
        const now = new Date();
        const daysAgo = {
          week: 7,
          month: 30,
          quarter: 90
        }[filterDateRange];

        const cutoffDate = new Date(now.getTime() - (daysAgo * 24 * 60 * 60 * 1000));
        matchesDate = entryDate >= cutoffDate;
      }

      return matchesSearch && matchesMood && matchesDate;
    });

    return filtered.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [entries, searchTerm, filterMood, filterDateRange]);

  // Group entries by date for timeline visualization
  const groupedEntries = useMemo(() => {
    const groups: { [key: string]: JournalEntry[] } = {};

    filteredEntries.forEach(entry => {
      const dateKey = new Date(entry.date).toDateString();
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(entry);
    });

    return Object.entries(groups).sort((a, b) => 
      new Date(b[0]).getTime() - new Date(a[0]).getTime()
    );
  }, [filteredEntries]);

  const getMoodColor = (mood?: string) => {
    switch (mood) {
      case 'excellent': return 'bg-green-500';
      case 'good': return 'bg-green-300';
      case 'neutral': return 'bg-yellow-300';
      case 'poor': return 'bg-orange-400';
      case 'terrible': return 'bg-red-500';
      default: return 'bg-gray-400';
    }
  };

  const getMoodIcon = (mood?: string) => {
    switch (mood) {
      case 'excellent':
      case 'good':
        return <TrendingUp size={16} className="text-green-600" />;
      case 'poor':
      case 'terrible':
        return <TrendingDown size={16} className="text-red-600" />;
      default:
        return <Minus size={16} className="text-gray-600" />;
    }
  };

  const calculateDayPnL = (trades?: JournalEntry['trades']) => {
    if (!trades || trades.length === 0) return 0;
    return trades.reduce((sum, trade) => sum + trade.pnl, 0);
  };

  const renderEntry = (entry: JournalEntry) => {
    const dayPnL = calculateDayPnL(entry.trades);

    return (
      <div
        key={entry.id}
        className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
        onClick={() => onEntryClick?.(entry)}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getMoodColor(entry.mood)}`} />
            <h3 className="font-medium text-gray-900">{entry.title}</h3>
            {getMoodIcon(entry.mood)}
          </div>
          <div className="text-sm text-gray-500">
            {new Date(entry.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>

        {/* Content Preview */}
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {entry.content.substring(0, 150)}
          {entry.content.length > 150 && '...'}
        </p>

        {/* Metrics Row */}
        <div className="flex items-center justify-between mb-3">
          {entry.confidence && (
            <div className="flex items-center gap-1">
              <span className="text-xs text-gray-500">Confidence:</span>
              <div className="flex">
                {[...Array(10)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-2 h-2 rounded-full mr-0.5 ${
                      i < entry.confidence! ? 'bg-blue-500' : 'bg-gray-200'
                    }`}
                  />
                ))}
              </div>
              <span className="text-xs text-gray-600">{entry.confidence}/10</span>
            </div>
          )}

          {entry.trades && entry.trades.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">P&L:</span>
              <span className={`text-sm font-medium ${
                dayPnL >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {dayPnL >= 0 ? '+' : ''}${dayPnL.toFixed(2)}
              </span>
            </div>
          )}
        </div>

        {/* Trades Summary */}
        {entry.trades && entry.trades.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {entry.trades.slice(0, 3).map((trade, index) => (
              <span
                key={index}
                className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                  trade.pnl >= 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}
              >
                {trade.direction === 'long' ? (
                  <ArrowUpRight size={10} className="mr-1" />
                ) : (
                  <ArrowDownRight size={10} className="mr-1" />
                )}
                {trade.symbol}
                <span className="ml-1">
                  {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(0)}
                </span>
              </span>
            ))}
            {entry.trades.length > 3 && (
              <span className="text-xs text-gray-500">
                +{entry.trades.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Tags */}
        {entry.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {entry.tags.slice(0, 4).map(tag => (
              <span
                key={tag}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700"
              >
                #{tag}
              </span>
            ))}
            {entry.tags.length > 4 && (
              <span className="text-xs text-gray-500">
                +{entry.tags.length - 4} more
              </span>
            )}
          </div>
        )}

        {/* Market Context */}
        {entry.marketContext && (
          <div className="text-xs text-gray-500 border-t pt-2">
            Market: {entry.marketContext.regime} • 
            Volatility: {entry.marketContext.volatility} • 
            Sentiment: {entry.marketContext.sentiment}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`journal-timeline ${className}`}>
      {/* Header with Search and Filters */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Journal Timeline</h2>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <Filter size={16} />
            Filters
          </button>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search size={20} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search journal entries..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="bg-gray-50 border rounded-lg p-4 mb-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Mood Filter
                </label>
                <select
                  value={filterMood}
                  onChange={(e) => setFilterMood(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Moods</option>
                  <option value="excellent">Excellent</option>
                  <option value="good">Good</option>
                  <option value="neutral">Neutral</option>
                  <option value="poor">Poor</option>
                  <option value="terrible">Terrible</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Date Range
                </label>
                <select
                  value={filterDateRange}
                  onChange={(e) => setFilterDateRange(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Time</option>
                  <option value="week">Last Week</option>
                  <option value="month">Last Month</option>
                  <option value="quarter">Last Quarter</option>
                </select>
              </div>
            </div>
          </div>
        )}

        <div className="text-sm text-gray-600">
          Showing {filteredEntries.length} of {entries.length} entries
        </div>
      </div>

      {/* Timeline */}
      {groupedEntries.length === 0 ? (
        <div className="text-center py-12">
          <Calendar size={48} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No entries found</h3>
          <p className="text-gray-600">
            {searchTerm || filterMood !== 'all' || filterDateRange !== 'all'
              ? "Try adjusting your filters to see more entries."
              : "Start journaling your trading journey!"}
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {groupedEntries.map(([date, dayEntries]) => (
            <div key={date} className="relative">
              {/* Date Header */}
              <div className="flex items-center mb-4">
                <div className="flex items-center justify-center w-10 h-10 bg-blue-500 text-white rounded-full text-sm font-medium">
                  {new Date(date).getDate()}
                </div>
                <div className="ml-4">
                  <div className="font-medium text-gray-900">
                    {new Date(date).toLocaleDateString('en-US', { 
                      weekday: 'long', 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </div>
                  <div className="text-sm text-gray-600">
                    {dayEntries.length} entr{dayEntries.length !== 1 ? 'ies' : 'y'}
                  </div>
                </div>
              </div>

              {/* Entries for this date */}
              <div className="ml-14 space-y-4">
                {dayEntries.map(entry => renderEntry(entry))}
              </div>

              {/* Timeline line */}
              <div className="absolute left-5 top-12 bottom-0 w-0.5 bg-gray-200" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default JournalTimeline;