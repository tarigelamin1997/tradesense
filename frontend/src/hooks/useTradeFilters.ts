import { useState, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

interface Trade {
  id: number;
  symbol: string;
  direction: 'long' | 'short';
  pnl: number;
  status: 'open' | 'closed';
  open_date: string;
  close_date?: string;
  notes?: string;
  tags?: string[];
}

export interface TradeFilters {
  search: string;
  status: 'all' | 'open' | 'closed';
  pnlFilter: 'all' | 'winners' | 'losers';
  symbol: string;
  side: 'all' | 'long' | 'short';
  dateFrom: string;
  dateTo: string;
  datePreset: string;
}

const DEFAULT_FILTERS: TradeFilters = {
  search: '',
  status: 'all',
  pnlFilter: 'all',
  symbol: '',
  side: 'all',
  dateFrom: '',
  dateTo: '',
  datePreset: 'all'
};

export const useTradeFilters = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Initialize filters from URL params
  const filters = useMemo<TradeFilters>(() => ({
    search: searchParams.get('search') || DEFAULT_FILTERS.search,
    status: (searchParams.get('status') || DEFAULT_FILTERS.status) as TradeFilters['status'],
    pnlFilter: (searchParams.get('pnl') || DEFAULT_FILTERS.pnlFilter) as TradeFilters['pnlFilter'],
    symbol: searchParams.get('symbol') || DEFAULT_FILTERS.symbol,
    side: (searchParams.get('side') || DEFAULT_FILTERS.side) as TradeFilters['side'],
    dateFrom: searchParams.get('from') || DEFAULT_FILTERS.dateFrom,
    dateTo: searchParams.get('to') || DEFAULT_FILTERS.dateTo,
    datePreset: searchParams.get('preset') || DEFAULT_FILTERS.datePreset
  }), [searchParams]);
  
  // Update URL params when filters change
  const updateFilters = useCallback((newFilters: Partial<TradeFilters>) => {
    const updatedFilters = { ...filters, ...newFilters };
    const params = new URLSearchParams();
    
    Object.entries(updatedFilters).forEach(([key, value]) => {
      if (value && value !== DEFAULT_FILTERS[key as keyof TradeFilters]) {
        params.set(key, value);
      }
    });
    
    setSearchParams(params);
  }, [filters, setSearchParams]);
  
  // Date preset handlers
  const applyDatePreset = useCallback((preset: string) => {
    const now = new Date();
    let from = '';
    let to = now.toISOString().split('T')[0];
    
    switch (preset) {
      case 'today':
        from = to;
        break;
      case 'week':
        const weekAgo = new Date(now);
        weekAgo.setDate(weekAgo.getDate() - 7);
        from = weekAgo.toISOString().split('T')[0];
        break;
      case 'month':
        const monthAgo = new Date(now);
        monthAgo.setMonth(monthAgo.getMonth() - 1);
        from = monthAgo.toISOString().split('T')[0];
        break;
      case '30days':
        const thirtyDaysAgo = new Date(now);
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        from = thirtyDaysAgo.toISOString().split('T')[0];
        break;
      case 'all':
      default:
        from = '';
        to = '';
        break;
    }
    
    updateFilters({
      dateFrom: from,
      dateTo: to,
      datePreset: preset
    });
  }, [updateFilters]);
  
  // Clear all filters
  const clearFilters = useCallback(() => {
    setSearchParams(new URLSearchParams());
  }, [setSearchParams]);
  
  // Filter trades
  const filterTrades = useCallback((trades: Trade[]) => {
    return trades.filter(trade => {
      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        const matchesSearch = 
          trade.symbol.toLowerCase().includes(searchLower) ||
          trade.notes?.toLowerCase().includes(searchLower) ||
          trade.id.toString().includes(searchLower) ||
          trade.tags?.some(tag => tag.toLowerCase().includes(searchLower));
        
        if (!matchesSearch) return false;
      }
      
      // Status filter
      if (filters.status !== 'all' && trade.status !== filters.status) {
        return false;
      }
      
      // P&L filter
      if (filters.pnlFilter !== 'all') {
        if (filters.pnlFilter === 'winners' && trade.pnl <= 0) return false;
        if (filters.pnlFilter === 'losers' && trade.pnl >= 0) return false;
      }
      
      // Symbol filter
      if (filters.symbol && trade.symbol !== filters.symbol) {
        return false;
      }
      
      // Side filter
      if (filters.side !== 'all' && trade.direction !== filters.side) {
        return false;
      }
      
      // Date range filter
      if (filters.dateFrom || filters.dateTo) {
        const tradeDate = new Date(trade.open_date).getTime();
        
        if (filters.dateFrom) {
          const fromDate = new Date(filters.dateFrom).getTime();
          if (tradeDate < fromDate) return false;
        }
        
        if (filters.dateTo) {
          const toDate = new Date(filters.dateTo + 'T23:59:59').getTime();
          if (tradeDate > toDate) return false;
        }
      }
      
      return true;
    });
  }, [filters]);
  
  // Count active filters
  const activeFilterCount = useMemo(() => {
    return Object.entries(filters).filter(([key, value]) => {
      if (key === 'datePreset') return false; // Don't count preset
      return value && value !== DEFAULT_FILTERS[key as keyof TradeFilters];
    }).length;
  }, [filters]);
  
  return {
    filters,
    updateFilters,
    clearFilters,
    filterTrades,
    applyDatePreset,
    activeFilterCount
  };
};