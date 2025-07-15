import React, { useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
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
import { useVirtualScroll } from '../hooks/useVirtualScroll';

interface Trade {
  id: number;
  symbol: string;
  direction: 'long' | 'short';
  pnl: number;
  pnl_percentage: number;
  entry_price: number;
  exit_price?: number;
  quantity: number;
  status: 'open' | 'closed';
  open_date: string;
  close_date?: string;
  duration?: number;
}

type SortField = 'date' | 'pnl' | 'symbol' | 'duration' | 'quantity';
type SortDirection = 'asc' | 'desc';

interface SortConfig {
  field: SortField;
  direction: SortDirection;
}

interface TradeTableProps {
  trades: Trade[];
  sortConfig: SortConfig;
  onSort: (field: SortField) => void;
  isSelected: (id: number) => boolean;
  onItemClick: (id: number, event: React.MouseEvent) => void;
  toggleSelection: (id: number) => void;
  toggleAll: () => void;
  isAllSelected: boolean;
  isPartiallySelected: boolean;
  enableVirtualScroll?: boolean;
}

const TradeTable: React.FC<TradeTableProps> = ({
  trades,
  sortConfig,
  onSort,
  isSelected,
  onItemClick,
  toggleSelection,
  toggleAll,
  isAllSelected,
  isPartiallySelected,
  enableVirtualScroll = false
}) => {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const tableRef = useRef<HTMLTableElement>(null);
  
  // Virtual scrolling for large datasets
  const virtualScroll = useVirtualScroll(trades, {
    itemHeight: 57, // Approximate height of a table row
    containerHeight: 600, // Fixed container height for virtual scrolling
    overscan: 5
  });
  
  const displayTrades = enableVirtualScroll && trades.length > 500 
    ? virtualScroll.visibleItems 
    : trades;
    
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
  
  // Set indeterminate state on checkbox
  useEffect(() => {
    const checkbox = tableRef.current?.querySelector('thead input[type="checkbox"]') as HTMLInputElement;
    if (checkbox) {
      checkbox.indeterminate = isPartiallySelected;
    }
  }, [isPartiallySelected]);
  
  const tableContent = (
    <table className="min-w-full bg-white" ref={tableRef}>
      <thead className="bg-gray-50 sticky top-0 z-10">
        <tr>
          <th className="px-6 py-3 text-left">
            <input
              type="checkbox"
              checked={isAllSelected}
              onChange={toggleAll}
              className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
            />
          </th>
          <th className="px-6 py-3 text-left">
            <button
              onClick={() => onSort('symbol')}
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
              onClick={() => onSort('quantity')}
              className="flex items-center space-x-1 text-xs font-medium text-gray-500 uppercase tracking-wider hover:text-gray-700"
            >
              <span>Quantity</span>
              <SortIcon field="quantity" />
            </button>
          </th>
          <th className="px-6 py-3 text-left">
            <button
              onClick={() => onSort('pnl')}
              className="flex items-center space-x-1 text-xs font-medium text-gray-500 uppercase tracking-wider hover:text-gray-700"
            >
              <span>P&L</span>
              <SortIcon field="pnl" />
            </button>
          </th>
          <th className="px-6 py-3 text-left">
            <button
              onClick={() => onSort('duration')}
              className="flex items-center space-x-1 text-xs font-medium text-gray-500 uppercase tracking-wider hover:text-gray-700"
            >
              <span>Duration</span>
              <SortIcon field="duration" />
            </button>
          </th>
          <th className="px-6 py-3 text-left">
            <button
              onClick={() => onSort('date')}
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
        {enableVirtualScroll && trades.length > 500 && (
          <tr style={{ height: virtualScroll.offsetY }} />
        )}
        {displayTrades.map((trade) => (
          <tr 
            key={trade.id} 
            className={`hover:bg-gray-50 cursor-pointer ${
              isSelected(trade.id) ? 'bg-blue-50' : ''
            }`}
            onClick={(e) => onItemClick(trade.id, e)}
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
        {enableVirtualScroll && trades.length > 500 && (
          <tr style={{ height: virtualScroll.totalHeight - virtualScroll.offsetY - (displayTrades.length * 57) }} />
        )}
      </tbody>
    </table>
  );
  
  if (enableVirtualScroll && trades.length > 500) {
    return (
      <div 
        ref={containerRef}
        className="overflow-auto border border-gray-200 rounded-lg"
        style={{ maxHeight: '600px' }}
        onScroll={virtualScroll.handleScroll}
      >
        {tableContent}
      </div>
    );
  }
  
  return (
    <div className="overflow-x-auto border border-gray-200 rounded-lg">
      {tableContent}
    </div>
  );
};

export default TradeTable;