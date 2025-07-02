
import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../../../components/ui/Card';
import { tradeSearchService, SearchFilters, SearchResult, FilterOptions } from '../../../services/tradeSearch';
import { useDebounce } from '../../../hooks/useDebounce';

interface TradeSearchDashboardProps {
  className?: string;
}

export const TradeSearchDashboard: React.FC<TradeSearchDashboardProps> = ({
  className = ''
}) => {
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Search and filter state
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    tags: [],
    instruments: [],
    strategies: [],
    winOnly: undefined,
    lossOnly: undefined,
    startDate: '',
    endDate: '',
    minPnl: undefined,
    maxPnl: undefined,
    limit: 50,
    offset: 0
  });

  // Debounce search query to avoid excessive API calls
  const debouncedQuery = useDebounce(filters.query, 300);

  useEffect(() => {
    loadFilterOptions();
  }, []);

  useEffect(() => {
    searchTrades();
  }, [debouncedQuery, filters.tags, filters.instruments, filters.strategies, 
      filters.winOnly, filters.lossOnly, filters.startDate, filters.endDate, 
      filters.minPnl, filters.maxPnl]);

  const loadFilterOptions = async () => {
    try {
      const options = await tradeSearchService.getFilterOptions();
      setFilterOptions(options);
    } catch (err) {
      console.error('Failed to load filter options:', err);
    }
  };

  const searchTrades = async () => {
    try {
      setLoading(true);
      setError(null);
      const results = await tradeSearchService.searchTrades({
        ...filters,
        query: debouncedQuery
      });
      setSearchResults(results);
    } catch (err) {
      console.error('Search failed:', err);
      setError('Failed to search trades');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = useCallback((key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      offset: 0 // Reset pagination when filters change
    }));
  }, []);

  const handleTagToggle = (tag: string) => {
    const currentTags = filters.tags || [];
    const newTags = currentTags.includes(tag)
      ? currentTags.filter(t => t !== tag)
      : [...currentTags, tag];
    handleFilterChange('tags', newTags);
  };

  const handleInstrumentToggle = (instrument: string) => {
    const currentInstruments = filters.instruments || [];
    const newInstruments = currentInstruments.includes(instrument)
      ? currentInstruments.filter(i => i !== instrument)
      : [...currentInstruments, instrument];
    handleFilterChange('instruments', newInstruments);
  };

  const handleStrategyToggle = (strategy: string) => {
    const currentStrategies = filters.strategies || [];
    const newStrategies = currentStrategies.includes(strategy)
      ? currentStrategies.filter(s => s !== strategy)
      : [...currentStrategies, strategy];
    handleFilterChange('strategies', newStrategies);
  };

  const clearAllFilters = () => {
    setFilters({
      query: '',
      tags: [],
      instruments: [],
      strategies: [],
      winOnly: undefined,
      lossOnly: undefined,
      startDate: '',
      endDate: '',
      minPnl: undefined,
      maxPnl: undefined,
      limit: 50,
      offset: 0
    });
  };

  const formatPnL = (pnl: number) => {
    const sign = pnl >= 0 ? '+' : '';
    return `${sign}$${pnl.toFixed(2)}`;
  };

  const getPnLColor = (pnl: number) => {
    return pnl >= 0 ? 'text-green-600' : 'text-red-600';
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Trade Journal Search</h2>
        <button
          onClick={clearAllFilters}
          className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
        >
          Clear All Filters
        </button>
      </div>

      {/* Search and Filters */}
      <Card className="p-6">
        <div className="space-y-4">
          {/* Search Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Notes, Strategy, or Tags
            </label>
            <input
              type="text"
              value={filters.query || ''}
              onChange={(e) => handleFilterChange('query', e.target.value)}
              placeholder="Search for keywords in your trades..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Filter Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Tags Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
              <div className="max-h-32 overflow-y-auto border border-gray-200 rounded p-2 space-y-1">
                {filterOptions?.tags.map(tag => (
                  <label key={tag} className="flex items-center text-sm">
                    <input
                      type="checkbox"
                      checked={filters.tags?.includes(tag) || false}
                      onChange={() => handleTagToggle(tag)}
                      className="mr-2"
                    />
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                      {tag}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Instruments Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Instruments</label>
              <div className="max-h-32 overflow-y-auto border border-gray-200 rounded p-2 space-y-1">
                {filterOptions?.instruments.map(instrument => (
                  <label key={instrument} className="flex items-center text-sm">
                    <input
                      type="checkbox"
                      checked={filters.instruments?.includes(instrument) || false}
                      onChange={() => handleInstrumentToggle(instrument)}
                      className="mr-2"
                    />
                    {instrument}
                  </label>
                ))}
              </div>
            </div>

            {/* Strategies Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Strategies</label>
              <div className="max-h-32 overflow-y-auto border border-gray-200 rounded p-2 space-y-1">
                {filterOptions?.strategies.map(strategy => (
                  <label key={strategy} className="flex items-center text-sm">
                    <input
                      type="checkbox"
                      checked={filters.strategies?.includes(strategy) || false}
                      onChange={() => handleStrategyToggle(strategy)}
                      className="mr-2"
                    />
                    {strategy}
                  </label>
                ))}
              </div>
            </div>

            {/* Win/Loss Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Outcome</label>
              <div className="space-y-2">
                <label className="flex items-center text-sm">
                  <input
                    type="radio"
                    name="outcome"
                    checked={filters.winOnly === true}
                    onChange={() => handleFilterChange('winOnly', true)}
                    className="mr-2"
                  />
                  Wins Only
                </label>
                <label className="flex items-center text-sm">
                  <input
                    type="radio"
                    name="outcome"
                    checked={filters.lossOnly === true}
                    onChange={() => handleFilterChange('lossOnly', true)}
                    className="mr-2"
                  />
                  Losses Only
                </label>
                <label className="flex items-center text-sm">
                  <input
                    type="radio"
                    name="outcome"
                    checked={!filters.winOnly && !filters.lossOnly}
                    onChange={() => {
                      handleFilterChange('winOnly', undefined);
                      handleFilterChange('lossOnly', undefined);
                    }}
                    className="mr-2"
                  />
                  All Trades
                </label>
              </div>
            </div>
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
              <input
                type="date"
                value={filters.startDate || ''}
                onChange={(e) => handleFilterChange('startDate', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
              <input
                type="date"
                value={filters.endDate || ''}
                onChange={(e) => handleFilterChange('endDate', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Results */}
      <Card className="p-6">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-2">Searching trades...</p>
          </div>
        ) : error ? (
          <div className="text-center py-8 text-red-600">
            <p>{error}</p>
          </div>
        ) : (
          <>
            {/* Results Header */}
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">
                {searchResults?.pagination.total || 0} trades found
              </h3>
              {searchResults && searchResults.pagination.total > 0 && (
                <p className="text-sm text-gray-600">
                  Showing {searchResults.pagination.offset + 1} to{' '}
                  {Math.min(
                    searchResults.pagination.offset + searchResults.pagination.limit,
                    searchResults.pagination.total
                  )}{' '}
                  of {searchResults.pagination.total}
                </p>
              )}
            </div>

            {/* Trade Cards */}
            <div className="space-y-4">
              {searchResults?.trades.map(trade => (
                <div
                  key={trade.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="font-semibold text-lg">{trade.symbol}</span>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          trade.direction === 'long' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {trade.direction.toUpperCase()}
                        </span>
                        {trade.strategyTag && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                            {trade.strategyTag}
                          </span>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 mb-3">
                        <div>
                          <span className="font-medium">Quantity:</span> {trade.quantity}
                        </div>
                        <div>
                          <span className="font-medium">Entry:</span> ${trade.entryPrice}
                        </div>
                        <div>
                          <span className="font-medium">Exit:</span> {trade.exitPrice ? `$${trade.exitPrice}` : 'Open'}
                        </div>
                        <div>
                          <span className="font-medium">Date:</span> {new Date(trade.entryTime).toLocaleDateString()}
                        </div>
                      </div>

                      {trade.notes && (
                        <div className="mb-3">
                          <p className="text-sm text-gray-700 italic">"{trade.notes}"</p>
                        </div>
                      )}

                      {trade.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-2">
                          {trade.tags.map(tag => (
                            <span
                              key={tag}
                              className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                            >
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="text-right">
                      {trade.pnl !== undefined && (
                        <div className={`text-lg font-bold ${getPnLColor(trade.pnl)}`}>
                          {formatPnL(trade.pnl)}
                        </div>
                      )}
                      {trade.confidenceScore && (
                        <div className="text-xs text-gray-500 mt-1">
                          Confidence: {trade.confidenceScore}/10
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {searchResults && searchResults.pagination.hasMore && (
              <div className="text-center mt-6">
                <button
                  onClick={() => handleFilterChange('offset', searchResults.pagination.offset + searchResults.pagination.limit)}
                  className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  Load More
                </button>
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
};

export default TradeSearchDashboard;
