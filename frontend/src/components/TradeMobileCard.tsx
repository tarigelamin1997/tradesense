import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  CheckCircle, 
  XCircle,
  MoreVertical
} from 'lucide-react';

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

interface TradeMobileCardProps {
  trade: Trade;
  isSelected: boolean;
  onSelect: () => void;
  onQuickAction?: (action: string) => void;
}

const TradeMobileCard: React.FC<TradeMobileCardProps> = ({
  trade,
  isSelected,
  onSelect
}) => {
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
      return `${diffMinutes}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffHours < 48) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  const formatDuration = (hours?: number) => {
    if (!hours) return '-';
    if (hours < 1) return `${Math.round(hours * 60)}m`;
    if (hours < 24) return `${hours.toFixed(1)}h`;
    const days = Math.floor(hours / 24);
    return `${days}d`;
  };

  return (
    <div 
      className={`bg-white border rounded-lg p-4 mb-3 transition-all ${
        isSelected ? 'border-blue-500 shadow-md' : 'border-gray-200'
      }`}
      onClick={onSelect}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          {/* Selection Checkbox */}
          <input
            type="checkbox"
            checked={isSelected}
            onChange={onSelect}
            onClick={(e) => e.stopPropagation()}
            className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
          />
          
          {/* Symbol and Direction */}
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-semibold text-gray-900">{trade.symbol}</h3>
              <div className="flex items-center">
                {trade.direction === 'long' ? (
                  <TrendingUp className="w-4 h-4 text-green-500" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-500" />
                )}
                <span className={`text-xs font-medium ml-1 ${
                  trade.direction === 'long' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {trade.direction.toUpperCase()}
                </span>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-0.5">{formatDate(trade.open_date)}</p>
          </div>
        </div>
        
        {/* Status Badge */}
        <div className="flex items-center space-x-2">
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
            trade.status === 'open' 
              ? 'bg-blue-100 text-blue-800' 
              : trade.pnl >= 0 
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
          }`}>
            {trade.status === 'open' ? (
              <>
                <Clock className="w-3 h-3 mr-0.5" />
                Open
              </>
            ) : trade.pnl >= 0 ? (
              <>
                <CheckCircle className="w-3 h-3 mr-0.5" />
                Win
              </>
            ) : (
              <>
                <XCircle className="w-3 h-3 mr-0.5" />
                Loss
              </>
            )}
          </span>
          
          {/* More Actions */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              // Show action menu
            }}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <MoreVertical className="w-4 h-4 text-gray-500" />
          </button>
        </div>
      </div>
      
      {/* Trade Details */}
      <div className="grid grid-cols-2 gap-3">
        {/* Entry/Exit */}
        <div>
          <p className="text-xs text-gray-500">Entry → Exit</p>
          <p className="text-sm font-medium">
            ${trade.entry_price.toFixed(2)}
            {trade.exit_price && (
              <> → ${trade.exit_price.toFixed(2)}</>
            )}
          </p>
        </div>
        
        {/* Quantity */}
        <div>
          <p className="text-xs text-gray-500">Quantity</p>
          <p className="text-sm font-medium">{trade.quantity}</p>
        </div>
        
        {/* P&L */}
        <div>
          <p className="text-xs text-gray-500">P&L</p>
          <p className={`text-sm font-bold ${
            trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {formatCurrency(trade.pnl)}
            <span className="text-xs font-normal ml-1">
              ({formatPercentage(trade.pnl_percentage)})
            </span>
          </p>
        </div>
        
        {/* Duration */}
        <div>
          <p className="text-xs text-gray-500">Duration</p>
          <p className="text-sm font-medium flex items-center">
            <Clock className="w-3 h-3 mr-1 text-gray-400" />
            {formatDuration(trade.duration)}
          </p>
        </div>
      </div>
    </div>
  );
};

export default TradeMobileCard;