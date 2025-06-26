
import React, { useState, useEffect } from 'react';
import { playbooksService, Playbook } from '../../../services/playbooks';

interface PlaybookSelectorProps {
  selectedPlaybookId?: string;
  onPlaybookChange: (playbookId: string | null) => void;
  className?: string;
}

export const PlaybookSelector: React.FC<PlaybookSelectorProps> = ({
  selectedPlaybookId,
  onPlaybookChange,
  className = ''
}) => {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    loadPlaybooks();
  }, []);

  const loadPlaybooks = async () => {
    try {
      setLoading(true);
      const data = await playbooksService.getPlaybooks({
        status: 'active',
        sort_by: 'name',
        sort_order: 'asc'
      });
      setPlaybooks(data);
    } catch (err) {
      console.error('Error loading playbooks:', err);
    } finally {
      setLoading(false);
    }
  };

  const selectedPlaybook = playbooks.find(p => p.id === selectedPlaybookId);

  if (loading) {
    return (
      <div className={className}>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Trading Playbook
        </label>
        <div className="animate-pulse bg-gray-200 h-10 rounded-md"></div>
      </div>
    );
  }

  return (
    <div className={className}>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Trading Playbook
        <span className="text-gray-500 text-xs ml-1">(Optional)</span>
      </label>
      
      <select
        value={selectedPlaybookId || ''}
        onChange={(e) => onPlaybookChange(e.target.value || null)}
        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">No playbook selected</option>
        {playbooks.map((playbook) => (
          <option key={playbook.id} value={playbook.id}>
            {playbook.name} ({playbook.total_trades} trades, {(parseFloat(playbook.win_rate) * 100).toFixed(0)}% win rate)
          </option>
        ))}
      </select>

      {playbooks.length === 0 && (
        <p className="text-sm text-gray-500 mt-1">
          No playbooks available. 
          <button
            type="button"
            onClick={() => setShowCreateForm(true)}
            className="text-blue-600 hover:text-blue-800 ml-1"
          >
            Create your first playbook
          </button>
        </p>
      )}

      {selectedPlaybook && (
        <div className="mt-2 p-3 bg-blue-50 rounded-md border border-blue-200">
          <h4 className="text-sm font-medium text-blue-900 mb-1">{selectedPlaybook.name}</h4>
          <div className="text-xs text-blue-700 space-y-1">
            <p><strong>Entry:</strong> {selectedPlaybook.entry_criteria}</p>
            <p><strong>Exit:</strong> {selectedPlaybook.exit_criteria}</p>
            {selectedPlaybook.description && (
              <p><strong>Notes:</strong> {selectedPlaybook.description}</p>
            )}
          </div>
          <div className="mt-2 flex gap-4 text-xs text-blue-600">
            <span>Trades: {selectedPlaybook.total_trades}</span>
            <span>Win Rate: {(parseFloat(selectedPlaybook.win_rate) * 100).toFixed(1)}%</span>
            <span>Avg P&L: ${parseFloat(selectedPlaybook.avg_pnl).toFixed(2)}</span>
          </div>
        </div>
      )}
    </div>
  );
};
