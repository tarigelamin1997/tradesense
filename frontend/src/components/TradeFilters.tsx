import React, { useState } from 'react';
import { 
  Filter, 
  Search, 
  X, 
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { TradeFilters as FilterType } from '../hooks/useTradeFilters';

interface TradeFiltersProps {
  filters: FilterType;
  onFilterChange: (filters: Partial<FilterType>) => void;
  onClearFilters: () => void;
  onDatePresetChange: (preset: string) => void;
  activeFilterCount: number;
  symbols: string[];
}

const TradeFilters: React.FC<TradeFiltersProps> = ({
  filters,
  onFilterChange,
  onClearFilters,
  onDatePresetChange,
  activeFilterCount,
  symbols
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const datePresets = [
    { value: 'all', label: 'All Time' },
    { value: 'today', label: 'Today' },
    { value: 'week', label: 'This Week' },
    { value: 'month', label: 'This Month' },
    { value: '30days', label: 'Last 30 Days' }
  ];
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Filter className="w-5 h-5 text-gray-500" />
          <h3 className="font-medium text-gray-900">Filters</h3>
          {activeFilterCount > 0 && (
            <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-600 rounded-full">
              {activeFilterCount} active
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {activeFilterCount > 0 && (
            <button
              onClick={onClearFilters}
              className="text-sm text-gray-500 hover:text-gray-700 flex items-center space-x-1"
            >
              <X className="w-4 h-4" />
              <span>Clear all</span>
            </button>
          )}
          
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 hover:bg-gray-100 rounded transition-colors"
          >
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </button>
        </div>
      </div>
      
      {/* Search Bar - Always visible */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={filters.search}
          onChange={(e) => onFilterChange({ search: e.target.value })}
          placeholder="Search by symbol, ID, or notes..."
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      
      {/* Expanded Filters */}
      {isExpanded && (
        <div className="space-y-4">
          {/* Date Presets */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date Range
            </label>
            <div className="flex flex-wrap gap-2">
              {datePresets.map(preset => (
                <button
                  key={preset.value}
                  onClick={() => onDatePresetChange(preset.value)}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                    filters.datePreset === preset.value
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            
            {/* Custom Date Range */}
            <div className="grid grid-cols-2 gap-3 mt-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">From</label>
                <input
                  type="date"
                  value={filters.dateFrom}
                  onChange={(e) => onFilterChange({ dateFrom: e.target.value, datePreset: 'custom' })}
                  className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">To</label>
                <input
                  type="date"
                  value={filters.dateTo}
                  onChange={(e) => onFilterChange({ dateTo: e.target.value, datePreset: 'custom' })}
                  className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
          
          {/* Filter Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={filters.status}
                onChange={(e) => onFilterChange({ status: e.target.value as any })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All</option>
                <option value="open">Open</option>
                <option value="closed">Closed</option>
              </select>
            </div>
            
            {/* P&L Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                P&L
              </label>
              <select
                value={filters.pnlFilter}
                onChange={(e) => onFilterChange({ pnlFilter: e.target.value as any })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All</option>
                <option value="winners">Winners Only</option>
                <option value="losers">Losers Only</option>
              </select>
            </div>
            
            {/* Symbol Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Symbol
              </label>
              <select
                value={filters.symbol}
                onChange={(e) => onFilterChange({ symbol: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Symbols</option>
                {symbols.map(symbol => (
                  <option key={symbol} value={symbol}>{symbol}</option>
                ))}
              </select>
            </div>
            
            {/* Side Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Side
              </label>
              <select
                value={filters.side}
                onChange={(e) => onFilterChange({ side: e.target.value as any })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All</option>
                <option value="long">Long</option>
                <option value="short">Short</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TradeFilters;