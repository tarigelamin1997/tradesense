import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTrades } from '../services/trades';
import { 
  AlertCircle, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  CheckCircle, 
  XCircle,
  ChevronUp,
  ChevronDown,
  MoreVertical,
  Eye
} from 'lucide-react';
import TradeStatistics from './TradeStatistics';
import TradeFilters from './TradeFilters';
import TradeBulkActions from './TradeBulkActions';
import TradeMobileCard from './TradeMobileCard';
import { useTradeFilters } from '../hooks/useTradeFilters';
import { useBulkSelection } from '../hooks/useBulkSelection';


type SortField = 'date' | 'pnl' | 'symbol' | 'duration' | 'quantity';
type SortDirection = 'asc' | 'desc';

interface SortConfig {
  field: SortField;
  direction: SortDirection;
}

function TradeLog() {
  const navigate = useNavigate();
  const [trades, setTrades] = useState<any[]>([]); // Using any[] to avoid type conflicts
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortConfig, setSortConfig] = useState<SortConfig>({ field: 'date', direction: 'desc' });
  const [isMobile, setIsMobile] = useState(window.innerWidth < 640);
  
  // Custom hooks
  const { 
    filters, 
    updateFilters, 
    clearFilters, 
    filterTrades, 
    applyDatePreset,
    activeFilterCount 
  } = useTradeFilters();
  
  // Load trades
  useEffect(() => {
    loadTrades();
  }, []);
  
  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 640);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const loadTrades = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getTrades();
      setTrades(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load trades');
      console.error('Error loading trades:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Filter and sort trades
  const processedTrades = useMemo(() => {
    const filtered = filterTrades(trades);
    
    // Sort trades
    const sorted = [...filtered].sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortConfig.field) {
        case 'pnl':
          aValue = a.pnl;
          bValue = b.pnl;
          break;
        case 'symbol':
          aValue = a.symbol;
          bValue = b.symbol;
          break;
        case 'duration':
          aValue = a.duration || 0;
          bValue = b.duration || 0;
          break;
        case 'quantity':
          aValue = a.quantity;
          bValue = b.quantity;
          break;
        case 'date':
        default:
          aValue = new Date(a.open_date).getTime();
          bValue = new Date(b.open_date).getTime();
          break;
      }
      
      if (sortConfig.direction === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
    
    return sorted;
  }, [trades, filters, sortConfig, filterTrades]);
  
  // Bulk selection
  const {
    selectedIds,
    selectedCount,
    isSelected,
    toggleSelection,
    handleItemClick,
    toggleAll,
    clearSelection,
    isAllSelected,
    isPartiallySelected
  } = useBulkSelection(processedTrades);
  
  // Get unique symbols for filter
  const uniqueSymbols = useMemo(() => {
    return Array.from(new Set(trades.map(t => t.symbol))).sort();
  }, [trades]);
  
  // Handle sort
  const handleSort = (field: SortField) => {
    setSortConfig(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'desc' ? 'asc' : 'desc'
    }));
  };
  
  // Bulk actions
  const handleBulkDelete = async () => {
    // Implement bulk delete
    console.log('Delete trades:', selectedIds);
    clearSelection();
  };
  
  const handleBulkExport = (format: 'csv' | 'excel') => {
    // Implement export
    console.log('Export trades:', selectedIds, format);
  };
  
  const handleBulkAddTags = (tags: string[]) => {
    // Implement add tags
    console.log('Add tags:', tags, 'to trades:', selectedIds);
  };
  
  const handleBulkArchive = () => {
    // Implement archive
    console.log('Archive trades:', selectedIds);
    clearSelection();
  };

  const formatCurrency = (amount: number) => {
    const formatted = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(Math.abs(amount));
    return amount >= 0 ? `+${formatted}` : `-${formatted}`;
  };

  const formatPercentage = (percentage: number) => {
    const formatted = Math.abs(percentage).toFixed(2);
    return percentage >= 0 ? `+${formatted}%` : `-${formatted}%`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffHours < 1) {
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      return `${diffMinutes} minutes ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hours ago`;
    } else if (diffHours < 48) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }
  };

  const formatDuration = (hours?: number) => {
    if (!hours) return '-';
    if (hours < 1) return `${Math.round(hours * 60)}m`;
    if (hours < 24) return `${hours.toFixed(1)}h`;
    const days = Math.floor(hours / 24);
    const remainingHours = hours % 24;
    return days > 0 ? `${days}d ${remainingHours.toFixed(0)}h` : `${hours.toFixed(1)}h`;
  };
  
  // Render sort icon
  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortConfig.field !== field) {
      return <ChevronUp className="w-4 h-4 text-gray-300" />;
    }
    return sortConfig.direction === 'desc' ? (
      <ChevronDown className="w-4 h-4 text-gray-600" />
    ) : (
      <ChevronUp className="w-4 h-4 text-gray-600" />
    );
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
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600">{error}</p>
          <button 
            onClick={loadTrades}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 pb-24">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Trade Log</h1>
        
        {/* Statistics */}
        <TradeStatistics trades={trades} loading={loading} />
        
        {/* Filters */}
        <TradeFilters
          filters={filters}
          onFilterChange={updateFilters}
          onClearFilters={clearFilters}
          onDatePresetChange={applyDatePreset}
          activeFilterCount={activeFilterCount}
          symbols={uniqueSymbols}
        />
      </div>

      {processedTrades.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">No trades found matching your filters</p>
          {activeFilterCount > 0 && (
            <button
              onClick={clearFilters}
              className="mt-4 text-blue-600 hover:text-blue-700"
            >
              Clear filters
            </button>
          )}
        </div>
      ) : (
        <>
          {/* Mobile View */}
          {isMobile ? (
            <div className="space-y-3">
              {processedTrades.map((trade) => (
                <TradeMobileCard
                  key={trade.id}
                  trade={trade}
                  isSelected={isSelected(trade.id)}
                  onSelect={() => toggleSelection(trade.id)}
                />
              ))}
            </div>
          ) : (
            /* Desktop Table View */
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white border border-gray-200 rounded-lg overflow-hidden">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={isAllSelected}
                        indeterminate={isPartiallySelected}
                        onChange={toggleAll}
                        className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                      />
                    </th>
                    <th className="px-6 py-3 text-left">
                      <button
                        onClick={() => handleSort('symbol')}
                        className="flex items-center space-x-1 text-xs font-medium text-gray-500 uppercase tracking-wider hover:text-gray-700"
                      >
                        <span>Symbol</span>
                        <SortIcon field="symbol" />
                      </button>
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Direction
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Entry/Exit
                    </th>
                    <th className="px-6 py-3 text-left">
                      <button
                        onClick={() => handleSort('quantity')}
                        className="flex items-center space-x-1 text-xs font-medium text-gray-500 uppercase tracking-wider hover:text-gray-700"
                      >
                        <span>Quantity</span>
                        <SortIcon field="quantity" />
                      </button>
                    </th>
                    <th className="px-6 py-3 text-left">
                      <button
                        onClick={() => handleSort('pnl')}
                        className="flex items-center space-x-1 text-xs font-medium text-gray-500 uppercase tracking-wider hover:text-gray-700"
                      >
                        <span>P&L</span>
                        <SortIcon field="pnl" />
                      </button>
                    </th>
                    <th className="px-6 py-3 text-left">
                      <button
                        onClick={() => handleSort('duration')}
                        className="flex items-center space-x-1 text-xs font-medium text-gray-500 uppercase tracking-wider hover:text-gray-700"
                      >
                        <span>Duration</span>
                        <SortIcon field="duration" />
                      </button>
                    </th>
                    <th className="px-6 py-3 text-left">
                      <button
                        onClick={() => handleSort('date')}
                        className="flex items-center space-x-1 text-xs font-medium text-gray-500 uppercase tracking-wider hover:text-gray-700"
                      >
                        <span>Date</span>
                        <SortIcon field="date" />
                      </button>
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {processedTrades.map((trade) => (
                    <tr 
                      key={trade.id} 
                      className={`hover:bg-gray-50 cursor-pointer ${
                        isSelected(trade.id) ? 'bg-blue-50' : ''
                      }`}
                      onClick={(e) => handleItemClick(trade.id, e)}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="checkbox"
                          checked={isSelected(trade.id)}
                          onChange={() => toggleSelection(trade.id)}
                          onClick={(e) => e.stopPropagation()}
                          className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{trade.symbol}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {trade.direction === 'long' ? (
                            <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                          ) : (
                            <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
                          )}
                          <span className={`text-sm font-medium ${
                            trade.direction === 'long' ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {trade.direction.toUpperCase()}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          ${trade.entry_price.toFixed(2)}
                          {trade.exit_price && (
                            <>
                              <span className="text-gray-500"> → </span>
                              ${trade.exit_price.toFixed(2)}
                            </>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{trade.quantity}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`text-sm font-medium ${
                          trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatCurrency(trade.pnl)}
                          <span className="text-xs ml-1">({formatPercentage(trade.pnl_percentage)})</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center text-sm text-gray-500">
                          <Clock className="w-3 h-3 mr-1" />
                          {formatDuration(trade.duration)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">
                          {formatDate(trade.open_date)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          trade.status === 'open' 
                            ? 'bg-blue-100 text-blue-800' 
                            : trade.pnl >= 0 
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                        }`}>
                          {trade.status === 'open' ? (
                            <>
                              <Clock className="w-3 h-3 mr-1" />
                              Open
                            </>
                          ) : trade.pnl >= 0 ? (
                            <>
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Win
                            </>
                          ) : (
                            <>
                              <XCircle className="w-3 h-3 mr-1" />
                              Loss
                            </>
                          )}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/trades/${trade.id}`);
                            }}
                            className="text-gray-400 hover:text-gray-600"
                            title="View details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              // Show more actions menu
                            }}
                            className="text-gray-400 hover:text-gray-600"
                          >
                            <MoreVertical className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
      
      <div className="mt-6 text-sm text-gray-500">
        <p>Showing {processedTrades.length} of {trades.length} trades</p>
      </div>
      
      {/* Bulk Actions */}
      <TradeBulkActions
        selectedCount={selectedCount}
        onDelete={handleBulkDelete}
        onExport={handleBulkExport}
        onAddTags={handleBulkAddTags}
        onArchive={handleBulkArchive}
        onClearSelection={clearSelection}
      />
    </div>
  );
}

export default TradeLog;