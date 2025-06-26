
import React, { useState, useEffect } from 'react';
import { playbooksService, Playbook, PlaybookCreate, PlaybookUpdate } from '../../../services/playbooks';

interface PlaybookManagerProps {
  onPlaybookSelect?: (playbook: Playbook) => void;
}

export const PlaybookManager: React.FC<PlaybookManagerProps> = ({ onPlaybookSelect }) => {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingPlaybook, setEditingPlaybook] = useState<Playbook | null>(null);
  const [sortBy, setSortBy] = useState('total_pnl');
  const [sortOrder, setSortOrder] = useState('desc');
  const [statusFilter, setStatusFilter] = useState('active');

  useEffect(() => {
    loadPlaybooks();
  }, [sortBy, sortOrder, statusFilter]);

  const loadPlaybooks = async () => {
    try {
      setLoading(true);
      const data = await playbooksService.getPlaybooks({
        status: statusFilter === 'all' ? undefined : statusFilter,
        sort_by: sortBy,
        sort_order: sortOrder,
        limit: 100
      });
      setPlaybooks(data);
    } catch (err) {
      setError('Failed to load playbooks');
      console.error('Error loading playbooks:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePlaybook = async (data: PlaybookCreate) => {
    try {
      await playbooksService.createPlaybook(data);
      setIsCreateModalOpen(false);
      loadPlaybooks();
    } catch (err) {
      setError('Failed to create playbook');
      console.error('Error creating playbook:', err);
    }
  };

  const handleUpdatePlaybook = async (id: string, data: PlaybookUpdate) => {
    try {
      await playbooksService.updatePlaybook(id, data);
      setEditingPlaybook(null);
      loadPlaybooks();
    } catch (err) {
      setError('Failed to update playbook');
      console.error('Error updating playbook:', err);
    }
  };

  const handleArchivePlaybook = async (id: string) => {
    if (window.confirm('Are you sure you want to archive this playbook?')) {
      try {
        await playbooksService.archivePlaybook(id);
        loadPlaybooks();
      } catch (err) {
        setError('Failed to archive playbook');
        console.error('Error archiving playbook:', err);
      }
    }
  };

  const handleDeletePlaybook = async (id: string) => {
    if (window.confirm('Are you sure you want to permanently delete this playbook? This cannot be undone.')) {
      try {
        await playbooksService.deletePlaybook(id);
        loadPlaybooks();
      } catch (err) {
        setError('Failed to delete playbook');
        console.error('Error deleting playbook:', err);
      }
    }
  };

  const getPerformanceColor = (totalPnl: string) => {
    const pnl = parseFloat(totalPnl);
    return pnl > 0 ? 'text-green-600' : pnl < 0 ? 'text-red-600' : 'text-gray-600';
  };

  const getWinRateColor = (winRate: string) => {
    const rate = parseFloat(winRate);
    if (rate >= 0.6) return 'text-green-600';
    if (rate >= 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Trading Playbooks</h2>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Create New Playbook
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Filters and Sorting */}
      <div className="mb-6 flex flex-wrap gap-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-2"
        >
          <option value="active">Active</option>
          <option value="archived">Archived</option>
          <option value="all">All</option>
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-2"
        >
          <option value="total_pnl">Total P&L</option>
          <option value="win_rate">Win Rate</option>
          <option value="name">Name</option>
          <option value="created_at">Created Date</option>
        </select>

        <select
          value={sortOrder}
          onChange={(e) => setSortOrder(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-2"
        >
          <option value="desc">Descending</option>
          <option value="asc">Ascending</option>
        </select>
      </div>

      {/* Playbooks Table */}
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Trades
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Win Rate
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Avg P&L
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total P&L
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
            {playbooks.map((playbook) => (
              <tr key={playbook.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{playbook.name}</div>
                    <div className="text-sm text-gray-500 truncate max-w-xs" title={playbook.description}>
                      {playbook.description || 'No description'}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {playbook.total_trades}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={getWinRateColor(playbook.win_rate)}>
                    {(parseFloat(playbook.win_rate) * 100).toFixed(1)}%
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={getPerformanceColor(playbook.avg_pnl)}>
                    ${parseFloat(playbook.avg_pnl).toFixed(2)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={getPerformanceColor(playbook.total_pnl)}>
                    ${parseFloat(playbook.total_pnl).toFixed(2)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    playbook.status === 'active' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {playbook.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <div className="flex gap-2">
                    <button
                      onClick={() => setEditingPlaybook(playbook)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Edit
                    </button>
                    {onPlaybookSelect && (
                      <button
                        onClick={() => onPlaybookSelect(playbook)}
                        className="text-green-600 hover:text-green-900"
                      >
                        Select
                      </button>
                    )}
                    <button
                      onClick={() => handleArchivePlaybook(playbook.id)}
                      className="text-yellow-600 hover:text-yellow-900"
                    >
                      Archive
                    </button>
                    <button
                      onClick={() => handleDeletePlaybook(playbook.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {playbooks.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No playbooks found</p>
          <p className="text-gray-400">Create your first trading playbook to get started</p>
        </div>
      )}

      {/* Create/Edit Modal */}
      {(isCreateModalOpen || editingPlaybook) && (
        <PlaybookModal
          playbook={editingPlaybook}
          onClose={() => {
            setIsCreateModalOpen(false);
            setEditingPlaybook(null);
          }}
          onSave={editingPlaybook ? 
            (data) => handleUpdatePlaybook(editingPlaybook.id, data) :
            handleCreatePlaybook
          }
        />
      )}
    </div>
  );
};

interface PlaybookModalProps {
  playbook?: Playbook | null;
  onClose: () => void;
  onSave: (data: PlaybookCreate | PlaybookUpdate) => void;
}

const PlaybookModal: React.FC<PlaybookModalProps> = ({ playbook, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: playbook?.name || '',
    entry_criteria: playbook?.entry_criteria || '',
    exit_criteria: playbook?.exit_criteria || '',
    description: playbook?.description || '',
    status: playbook?.status || 'active'
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          {playbook ? 'Edit Playbook' : 'Create New Playbook'}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Morning Breakout + High Volume"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Entry Criteria *
            </label>
            <textarea
              required
              rows={3}
              value={formData.entry_criteria}
              onChange={(e) => setFormData({ ...formData, entry_criteria: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., First 15min candle break + >2x average volume + RSI < 70"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Exit Criteria *
            </label>
            <textarea
              required
              rows={3}
              value={formData.exit_criteria}
              onChange={(e) => setFormData({ ...formData, exit_criteria: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., +1.5R target OR close below 9EMA OR end of trading session"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              rows={2}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Optional context, notes, or additional rules"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value as 'active' | 'archived' })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              {playbook ? 'Update' : 'Create'} Playbook
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
import React, { useState, useEffect } from 'react';
import { playbooksApi, Playbook, PlaybookCreate, PlaybookUpdate } from '../../../services/playbooks';

interface PlaybookFormData {
  name: string;
  entry_criteria: string;
  exit_criteria: string;
  description: string;
}

const PlaybookManager: React.FC = () => {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingPlaybook, setEditingPlaybook] = useState<Playbook | null>(null);
  const [includeArchived, setIncludeArchived] = useState(false);
  
  const [formData, setFormData] = useState<PlaybookFormData>({
    name: '',
    entry_criteria: '',
    exit_criteria: '',
    description: ''
  });

  useEffect(() => {
    loadPlaybooks();
  }, [includeArchived]);

  const loadPlaybooks = async () => {
    try {
      setLoading(true);
      const data = await playbooksApi.getPlaybooks(includeArchived);
      setPlaybooks(data);
    } catch (err) {
      setError('Failed to load playbooks');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingPlaybook) {
        const updateData: PlaybookUpdate = {
          name: formData.name,
          entry_criteria: formData.entry_criteria,
          exit_criteria: formData.exit_criteria,
          description: formData.description || undefined
        };
        await playbooksApi.updatePlaybook(editingPlaybook.id, updateData);
      } else {
        const createData: PlaybookCreate = {
          name: formData.name,
          entry_criteria: formData.entry_criteria,
          exit_criteria: formData.exit_criteria,
          description: formData.description || undefined
        };
        await playbooksApi.createPlaybook(createData);
      }
      
      setFormData({ name: '', entry_criteria: '', exit_criteria: '', description: '' });
      setShowForm(false);
      setEditingPlaybook(null);
      await loadPlaybooks();
    } catch (err) {
      setError('Failed to save playbook');
      console.error(err);
    }
  };

  const handleEdit = (playbook: Playbook) => {
    setEditingPlaybook(playbook);
    setFormData({
      name: playbook.name,
      entry_criteria: playbook.entry_criteria,
      exit_criteria: playbook.exit_criteria,
      description: playbook.description || ''
    });
    setShowForm(true);
  };

  const handleArchive = async (playbook: Playbook) => {
    try {
      await playbooksApi.updatePlaybook(playbook.id, { status: 'archived' });
      await loadPlaybooks();
    } catch (err) {
      setError('Failed to archive playbook');
      console.error(err);
    }
  };

  const handleRestore = async (playbook: Playbook) => {
    try {
      await playbooksApi.updatePlaybook(playbook.id, { status: 'active' });
      await loadPlaybooks();
    } catch (err) {
      setError('Failed to restore playbook');
      console.error(err);
    }
  };

  const resetForm = () => {
    setFormData({ name: '', entry_criteria: '', exit_criteria: '', description: '' });
    setShowForm(false);
    setEditingPlaybook(null);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">📋 Playbook Manager</h1>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={includeArchived}
                onChange={(e) => setIncludeArchived(e.target.checked)}
                className="mr-2"
              />
              Show archived
            </label>
            <button
              onClick={() => setShowForm(true)}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
            >
              ➕ New Playbook
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {showForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold mb-4">
                {editingPlaybook ? 'Edit Playbook' : 'Create New Playbook'}
              </h2>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Morning Breakout + High Volume"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Entry Criteria *
                  </label>
                  <textarea
                    value={formData.entry_criteria}
                    onChange={(e) => setFormData({ ...formData, entry_criteria: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="e.g., First 15min candle break + >2x average volume"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Exit Criteria *
                  </label>
                  <textarea
                    value={formData.exit_criteria}
                    onChange={(e) => setFormData({ ...formData, exit_criteria: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="e.g., +1.5R or close below 9EMA"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={2}
                    placeholder="Optional notes about this strategy..."
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={resetForm}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    {editingPlaybook ? 'Update' : 'Create'} Playbook
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {playbooks.map((playbook) => (
            <div
              key={playbook.id}
              className={`border rounded-lg p-4 ${
                playbook.status === 'archived' ? 'bg-gray-50 border-gray-300' : 'bg-white border-gray-200'
              }`}
            >
              <div className="flex justify-between items-start mb-3">
                <h3 className={`font-semibold ${playbook.status === 'archived' ? 'text-gray-500' : 'text-gray-900'}`}>
                  {playbook.name}
                </h3>
                <span className={`px-2 py-1 rounded text-xs ${
                  playbook.status === 'active' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {playbook.status}
                </span>
              </div>

              <div className="space-y-2 text-sm text-gray-600">
                <div>
                  <strong>Entry:</strong> {playbook.entry_criteria}
                </div>
                <div>
                  <strong>Exit:</strong> {playbook.exit_criteria}
                </div>
                {playbook.description && (
                  <div>
                    <strong>Notes:</strong> {playbook.description}
                  </div>
                )}
              </div>

              <div className="flex gap-2 mt-4">
                <button
                  onClick={() => handleEdit(playbook)}
                  className="flex-1 px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                >
                  Edit
                </button>
                {playbook.status === 'active' ? (
                  <button
                    onClick={() => handleArchive(playbook)}
                    className="flex-1 px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                  >
                    Archive
                  </button>
                ) : (
                  <button
                    onClick={() => handleRestore(playbook)}
                    className="flex-1 px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                  >
                    Restore
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {playbooks.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No playbooks yet</h3>
            <p className="text-gray-600 mb-4">
              Create your first playbook to start tracking your trading strategies
            </p>
            <button
              onClick={() => setShowForm(true)}
              className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors"
            >
              Create Your First Playbook
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PlaybookManager;
