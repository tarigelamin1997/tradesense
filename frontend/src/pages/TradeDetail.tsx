
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { journalService, TradeWithJournal } from '../services/journal';
import { JournalTimeline } from '../components/journal/JournalTimeline';

const TradeDetail: React.FC = () => {
  const { tradeId } = useParams<{ tradeId: string }>();
  const [trade, setTrade] = useState<TradeWithJournal | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (tradeId) {
      loadTradeDetail();
    }
  }, [tradeId]);

  const loadTradeDetail = async () => {
    if (!tradeId) return;
    
    try {
      setLoading(true);
      const data = await journalService.getTradeWithJournal(tradeId);
      setTrade(data);
    } catch (err) {
      setError('Failed to load trade details');
      console.error('Error loading trade:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !trade) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">{error || 'Trade not found'}</p>
        </div>
      </div>
    );
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getPnLColor = (pnl?: number) => {
    if (!pnl) return 'text-gray-600';
    return pnl >= 0 ? 'text-green-600' : 'text-red-600';
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Trade Summary Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {trade.symbol} - {trade.direction.toUpperCase()}
              </h1>
              <p className="text-gray-600">
                {trade.quantity} shares @ {formatCurrency(trade.entry_price)}
              </p>
            </div>
            
            {trade.pnl !== undefined && (
              <div className="text-right">
                <div className={`text-2xl font-bold ${getPnLColor(trade.pnl)}`}>
                  {formatCurrency(trade.pnl)}
                </div>
                <div className="text-sm text-gray-600">P&L</div>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-sm text-gray-600">Entry Time</div>
              <div className="font-medium">{formatDate(trade.entry_time)}</div>
            </div>
            
            {trade.exit_time && (
              <div className="bg-gray-50 p-4 rounded-md">
                <div className="text-sm text-gray-600">Exit Time</div>
                <div className="font-medium">{formatDate(trade.exit_time)}</div>
              </div>
            )}
            
            {trade.exit_price && (
              <div className="bg-gray-50 p-4 rounded-md">
                <div className="text-sm text-gray-600">Exit Price</div>
                <div className="font-medium">{formatCurrency(trade.exit_price)}</div>
              </div>
            )}
            
            {trade.strategy_tag && (
              <div className="bg-gray-50 p-4 rounded-md">
                <div className="text-sm text-gray-600">Strategy</div>
                <div className="font-medium">{trade.strategy_tag}</div>
              </div>
            )}
          </div>

          {trade.notes && (
            <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-md p-4">
              <div className="text-sm text-gray-600 mb-1">Trade Notes</div>
              <div className="text-gray-800">{trade.notes}</div>
            </div>
          )}
        </div>
      </div>

      {/* Journal Timeline */}
      <JournalTimeline
        tradeId={trade.id}
        onEntryAdded={() => {
          // Optionally refresh trade data
          loadTradeDetail();
        }}
      />
    </div>
  );
};

export default TradeDetail;
