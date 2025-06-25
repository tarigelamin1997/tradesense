
import React, { useState, useEffect } from 'react';
import { journalService, JournalEntry, JournalEntryCreate, JournalEntryUpdate } from '../../services/journal';

interface JournalTimelineProps {
  tradeId: string;
  onEntryAdded?: (entry: JournalEntry) => void;
  onEntryUpdated?: (entry: JournalEntry) => void;
  onEntryDeleted?: (entryId: string) => void;
}

export const JournalTimeline: React.FC<JournalTimelineProps> = ({
  tradeId,
  onEntryAdded,
  onEntryUpdated,
  onEntryDeleted
}) => {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingEntry, setEditingEntry] = useState<string | null>(null);

  useEffect(() => {
    loadJournalEntries();
  }, [tradeId]);

  const loadJournalEntries = async () => {
    try {
      setLoading(true);
      const data = await journalService.getTradeJournalEntries(tradeId);
      setEntries(data);
    } catch (err) {
      setError('Failed to load journal entries');
      console.error('Error loading journal entries:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddEntry = async (entryData: JournalEntryCreate) => {
    try {
      const newEntry = await journalService.createJournalEntry(tradeId, entryData);
      setEntries([newEntry, ...entries]);
      setShowAddForm(false);
      onEntryAdded?.(newEntry);
    } catch (err) {
      setError('Failed to create journal entry');
      console.error('Error creating journal entry:', err);
    }
  };

  const handleUpdateEntry = async (entryId: string, updateData: JournalEntryUpdate) => {
    try {
      const updatedEntry = await journalService.updateJournalEntry(entryId, updateData);
      setEntries(entries.map(entry => 
        entry.id === entryId ? updatedEntry : entry
      ));
      setEditingEntry(null);
      onEntryUpdated?.(updatedEntry);
    } catch (err) {
      setError('Failed to update journal entry');
      console.error('Error updating journal entry:', err);
    }
  };

  const handleDeleteEntry = async (entryId: string) => {
    if (!confirm('Are you sure you want to delete this journal entry?')) return;
    
    try {
      await journalService.deleteJournalEntry(entryId);
      setEntries(entries.filter(entry => entry.id !== entryId));
      onEntryDeleted?.(entryId);
    } catch (err) {
      setError('Failed to delete journal entry');
      console.error('Error deleting journal entry:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900">Trade Journal</h3>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
          >
            {showAddForm ? 'Cancel' : 'Add Entry'}
          </button>
        </div>
        
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}
      </div>

      {showAddForm && (
        <div className="p-6 border-b border-gray-200 bg-gray-50">
          <JournalEntryForm
            onSubmit={handleAddEntry}
            onCancel={() => setShowAddForm(false)}
          />
        </div>
      )}

      <div className="p-6">
        {entries.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 mb-2">
              <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <p className="text-gray-500">No journal entries yet. Start documenting your thoughts!</p>
          </div>
        ) : (
          <div className="space-y-6">
            {entries.map((entry, index) => (
              <div key={entry.id} className="relative">
                {index < entries.length - 1 && (
                  <div className="absolute left-4 top-12 w-0.5 h-full bg-gray-200"></div>
                )}
                
                <div className="flex space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
                    </div>
                  </div>
                  
                  <div className="flex-grow min-w-0">
                    {editingEntry === entry.id ? (
                      <JournalEntryForm
                        initialData={entry}
                        onSubmit={(data) => handleUpdateEntry(entry.id, data)}
                        onCancel={() => setEditingEntry(null)}
                      />
                    ) : (
                      <JournalEntryCard
                        entry={entry}
                        onEdit={() => setEditingEntry(entry.id)}
                        onDelete={() => handleDeleteEntry(entry.id)}
                      />
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

interface JournalEntryFormProps {
  initialData?: Partial<JournalEntry>;
  onSubmit: (data: JournalEntryCreate | JournalEntryUpdate) => void;
  onCancel: () => void;
}

const JournalEntryForm: React.FC<JournalEntryFormProps> = ({
  initialData,
  onSubmit,
  onCancel
}) => {
  const [title, setTitle] = useState(initialData?.title || '');
  const [content, setContent] = useState(initialData?.content || '');
  const [mood, setMood] = useState(initialData?.mood || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    
    onSubmit({ title: title.trim(), content: content.trim(), mood: mood || undefined });
  };

  const moodOptions = [
    { value: '', label: 'Select mood (optional)' },
    { value: 'confident', label: '😎 Confident' },
    { value: 'nervous', label: '😰 Nervous' },
    { value: 'excited', label: '🚀 Excited' },
    { value: 'cautious', label: '⚠️ Cautious' },
    { value: 'frustrated', label: '😤 Frustrated' },
    { value: 'satisfied', label: '😌 Satisfied' },
    { value: 'neutral', label: '😐 Neutral' }
  ];

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <input
          type="text"
          placeholder="Entry title..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>
      
      <div>
        <select
          value={mood}
          onChange={(e) => setMood(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {moodOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      
      <div>
        <textarea
          placeholder="What's on your mind about this trade?"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-vertical"
          required
        />
      </div>
      
      <div className="flex space-x-3">
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
        >
          {initialData ? 'Update' : 'Add'} Entry
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-md text-sm font-medium transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
};

interface JournalEntryCardProps {
  entry: JournalEntry;
  onEdit: () => void;
  onDelete: () => void;
}

const JournalEntryCard: React.FC<JournalEntryCardProps> = ({
  entry,
  onEdit,
  onDelete
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getMoodEmoji = (mood?: string) => {
    const moodMap: Record<string, string> = {
      confident: '😎',
      nervous: '😰',
      excited: '🚀',
      cautious: '⚠️',
      frustrated: '😤',
      satisfied: '😌',
      neutral: '😐'
    };
    return mood ? moodMap[mood] || '💭' : '💭';
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getMoodEmoji(entry.mood)}</span>
          <h4 className="font-medium text-gray-900">{entry.title}</h4>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={onEdit}
            className="text-gray-400 hover:text-blue-600 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            onClick={onDelete}
            className="text-gray-400 hover:text-red-600 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
      
      <p className="text-gray-700 mb-3 whitespace-pre-wrap">{entry.content}</p>
      
      <div className="flex justify-between items-center text-xs text-gray-500">
        <span>{formatDate(entry.timestamp)}</span>
        {entry.mood && (
          <span className="bg-gray-100 px-2 py-1 rounded-full capitalize">
            {entry.mood}
          </span>
        )}
      </div>
    </div>
  );
};
