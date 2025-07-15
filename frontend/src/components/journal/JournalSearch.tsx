import React, { useState, useCallback, useEffect } from 'react';
import { Search, Filter, Calendar, Tag, TrendingUp, Smile, X } from 'lucide-react';
import { format } from 'date-fns';
import Fuse from 'fuse.js';
import { JournalEntry } from '../../services/journal';

export interface SearchFilters {
  query: string;
  dateFrom?: Date;
  dateTo?: Date;
  hasTrades?: boolean;
  sentiment?: 'positive' | 'negative' | 'neutral';
  template?: string;
  tags?: string[];
  mood?: string;
}

interface JournalSearchProps {
  entries: JournalEntry[];
  onSearch: (results: JournalEntry[], filters: SearchFilters) => void;
  onClose?: () => void;
}

export const JournalSearch: React.FC<JournalSearchProps> = ({
  entries,
  onSearch,
  onClose
}) => {
  const [filters, setFilters] = useState<SearchFilters>({
    query: ''
  });
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [searchResults, setSearchResults] = useState<JournalEntry[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Configure Fuse.js for fuzzy search
  const fuse = new Fuse(entries, {
    keys: ['title', 'content'],
    threshold: 0.3,
    includeScore: true,
    ignoreLocation: true,
    minMatchCharLength: 2
  });

  // Parse search query for special syntax
  const parseSearchQuery = (query: string) => {
    const patterns = {
      exactPhrase: /"([^"]+)"/g,
      trade: /trade:(\S+)/g,
      mood: /mood:(\S+)/g,
      profit: /profit:([><=])(\d+)/g,
      tag: /tag:(\S+)/g
    };

    const parsed = {
      text: query,
      exactPhrases: [] as string[],
      trades: [] as string[],
      moods: [] as string[],
      profitCondition: null as { operator: string; value: number } | null,
      tags: [] as string[]
    };

    // Extract exact phrases
    let match;
    while ((match = patterns.exactPhrase.exec(query)) !== null) {
      parsed.exactPhrases.push(match[1]);
      parsed.text = parsed.text.replace(match[0], '');
    }

    // Extract trade symbols
    while ((match = patterns.trade.exec(query)) !== null) {
      parsed.trades.push(match[1].toUpperCase());
      parsed.text = parsed.text.replace(match[0], '');
    }

    // Extract moods
    while ((match = patterns.mood.exec(query)) !== null) {
      parsed.moods.push(match[1].toLowerCase());
      parsed.text = parsed.text.replace(match[0], '');
    }

    // Extract profit conditions
    match = patterns.profit.exec(query);
    if (match) {
      parsed.profitCondition = {
        operator: match[1],
        value: parseInt(match[2])
      };
      parsed.text = parsed.text.replace(match[0], '');
    }

    // Extract tags
    while ((match = patterns.tag.exec(query)) !== null) {
      parsed.tags.push(match[1]);
      parsed.text = parsed.text.replace(match[0], '');
    }

    parsed.text = parsed.text.trim();
    return parsed;
  };

  // Perform search
  const performSearch = useCallback(() => {
    setIsSearching(true);
    
    let results = [...entries];
    
    // Apply date filters
    if (filters.dateFrom) {
      results = results.filter(entry => 
        new Date(entry.created_at) >= filters.dateFrom!
      );
    }
    if (filters.dateTo) {
      results = results.filter(entry => 
        new Date(entry.created_at) <= filters.dateTo!
      );
    }
    
    // Apply mood filter
    if (filters.mood) {
      results = results.filter(entry => entry.mood === filters.mood);
    }
    
    // Apply sentiment filter (would need sentiment analysis)
    if (filters.sentiment) {
      // This would require sentiment analysis implementation
      // For now, we'll use a simple keyword approach
      results = results.filter(entry => {
        const content = (entry.content || '').toLowerCase();
        if (filters.sentiment === 'positive') {
          return content.includes('profit') || content.includes('win') || 
                 content.includes('success') || content.includes('great');
        } else if (filters.sentiment === 'negative') {
          return content.includes('loss') || content.includes('mistake') || 
                 content.includes('failed') || content.includes('bad');
        }
        return true;
      });
    }
    
    // Apply text search with special syntax
    if (filters.query) {
      const parsed = parseSearchQuery(filters.query);
      
      // Use Fuse.js for fuzzy text search
      if (parsed.text) {
        const fuseResults = fuse.search(parsed.text);
        results = results.filter(entry => 
          fuseResults.some(result => result.item.id === entry.id)
        );
      }
      
      // Apply exact phrase matching
      parsed.exactPhrases.forEach(phrase => {
        results = results.filter(entry => 
          entry.content.toLowerCase().includes(phrase.toLowerCase()) ||
          entry.title.toLowerCase().includes(phrase.toLowerCase())
        );
      });
      
      // Apply trade filtering
      if (parsed.trades.length > 0) {
        results = results.filter(entry =>
          parsed.trades.some(trade => 
            entry.content.includes(trade) || entry.title.includes(trade)
          )
        );
      }
      
      // Apply mood filtering from query
      if (parsed.moods.length > 0) {
        results = results.filter(entry =>
          entry.mood && parsed.moods.includes(entry.mood.toLowerCase())
        );
      }
    }
    
    setSearchResults(results);
    onSearch(results, filters);
    setIsSearching(false);
  }, [entries, filters, fuse, onSearch]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      performSearch();
    }, 300);
    
    return () => clearTimeout(timer);
  }, [filters, performSearch]);

  const handleFilterChange = (key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Search Journal</h3>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
      
      {/* Main search input */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={filters.query}
          onChange={(e) => handleFilterChange('query', e.target.value)}
          placeholder='Search entries... (use "quotes" for exact match, trade:AAPL, mood:happy)'
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className={`absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded ${
            showAdvanced ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'
          }`}
        >
          <Filter className="w-4 h-4" />
        </button>
      </div>
      
      {/* Advanced filters */}
      {showAdvanced && (
        <div className="space-y-4 mb-4 p-4 bg-gray-50 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Date range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Calendar className="inline w-4 h-4 mr-1" />
                Date From
              </label>
              <input
                type="date"
                value={filters.dateFrom ? format(filters.dateFrom, 'yyyy-MM-dd') : ''}
                onChange={(e) => handleFilterChange('dateFrom', e.target.value ? new Date(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Calendar className="inline w-4 h-4 mr-1" />
                Date To
              </label>
              <input
                type="date"
                value={filters.dateTo ? format(filters.dateTo, 'yyyy-MM-dd') : ''}
                onChange={(e) => handleFilterChange('dateTo', e.target.value ? new Date(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Mood filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Smile className="inline w-4 h-4 mr-1" />
                Mood
              </label>
              <select
                value={filters.mood || ''}
                onChange={(e) => handleFilterChange('mood', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Moods</option>
                <option value="confident">😎 Confident</option>
                <option value="happy">😊 Happy</option>
                <option value="neutral">😐 Neutral</option>
                <option value="anxious">😰 Anxious</option>
                <option value="frustrated">😤 Frustrated</option>
              </select>
            </div>
            
            {/* Sentiment filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <TrendingUp className="inline w-4 h-4 mr-1" />
                Sentiment
              </label>
              <select
                value={filters.sentiment || ''}
                onChange={(e) => handleFilterChange('sentiment', e.target.value as any || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Sentiments</option>
                <option value="positive">Positive</option>
                <option value="neutral">Neutral</option>
                <option value="negative">Negative</option>
              </select>
            </div>
            
            {/* Has trades filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Tag className="inline w-4 h-4 mr-1" />
                Has Trades
              </label>
              <select
                value={filters.hasTrades === undefined ? '' : filters.hasTrades.toString()}
                onChange={(e) => handleFilterChange('hasTrades', e.target.value === '' ? undefined : e.target.value === 'true')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Entries</option>
                <option value="true">With Trades</option>
                <option value="false">Without Trades</option>
              </select>
            </div>
          </div>
          
          <div className="flex justify-between items-center">
            <button
              onClick={() => setFilters({ query: '' })}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              Clear all filters
            </button>
            
            <div className="text-sm text-gray-500">
              {isSearching ? 'Searching...' : `${searchResults.length} results found`}
            </div>
          </div>
        </div>
      )}
      
      {/* Search syntax help */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <p className="text-xs text-blue-700">
          <strong>Search tips:</strong> Use "exact phrase" for exact matches, 
          trade:AAPL for specific symbols, mood:happy for mood filtering, 
          profit:{'>'}100 for profit conditions
        </p>
      </div>
    </div>
  );
};

export default JournalSearch;