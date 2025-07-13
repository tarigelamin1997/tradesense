import React, { useState, useEffect } from 'react';
import { journalService, JournalEntry, TradeWithJournal } from '../services/journal';
import { BookOpen, Calendar, Edit, Trash2, Plus, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';

interface MoodEmoji {
  [key: string]: string;
}

const moodEmojis: MoodEmoji = {
  confident: '😎',
  anxious: '😰',
  neutral: '😐',
  happy: '😊',
  frustrated: '😤',
  focused: '🎯',
  uncertain: '🤔'
};

function Journal() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [tradesWithJournal, setTradesWithJournal] = useState<TradeWithJournal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'entries' | 'trades'>('entries');
  const [showNewEntry, setShowNewEntry] = useState(false);
  const [newEntry, setNewEntry] = useState({
    title: '',
    content: '',
    mood: 'neutral'
  });

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (activeTab === 'entries') {
        const data = await journalService.getJournalEntries();
        setEntries(data);
      } else {
        const data = await journalService.getTradesWithJournal();
        setTradesWithJournal(data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load journal data');
      console.error('Error loading journal:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEntry = async () => {
    if (!newEntry.title || !newEntry.content) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      await journalService.createJournalEntry(newEntry);
      setShowNewEntry(false);
      setNewEntry({ title: '', content: '', mood: 'neutral' });
      loadData();
    } catch (err: any) {
      alert('Failed to create journal entry: ' + err.message);
    }
  };

  const handleDeleteEntry = async (id: string) => {
    if (!confirm('Are you sure you want to delete this entry?')) return;

    try {
      await journalService.deleteJournalEntry(id);
      loadData();
    } catch (err: any) {
      alert('Failed to delete entry: ' + err.message);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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
            onClick={loadData}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <BookOpen className="w-6 h-6 mr-2" />
            Trade Journal
          </h1>
          <button
            onClick={() => setShowNewEntry(!showNewEntry)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <Plus className="w-4 h-4 mr-1" />
            New Entry
          </button>
        </div>

        <div className="flex space-x-1 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('entries')}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'entries'
                ? 'text-blue-600 border-blue-600'
                : 'text-gray-500 border-transparent hover:text-gray-700'
            }`}
          >
            Journal Entries ({entries.length})
          </button>
          <button
            onClick={() => setActiveTab('trades')}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'trades'
                ? 'text-blue-600 border-blue-600'
                : 'text-gray-500 border-transparent hover:text-gray-700'
            }`}
          >
            Trades with Notes ({tradesWithJournal.length})
          </button>
        </div>
      </div>

      {showNewEntry && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">New Journal Entry</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title
              </label>
              <input
                type="text"
                value={newEntry.title}
                onChange={(e) => setNewEntry({ ...newEntry, title: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Entry title..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Mood
              </label>
              <select
                value={newEntry.mood}
                onChange={(e) => setNewEntry({ ...newEntry, mood: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {Object.entries(moodEmojis).map(([mood, emoji]) => (
                  <option key={mood} value={mood}>
                    {emoji} {mood.charAt(0).toUpperCase() + mood.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Content
              </label>
              <textarea
                value={newEntry.content}
                onChange={(e) => setNewEntry({ ...newEntry, content: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={4}
                placeholder="Write your thoughts..."
              />
            </div>
            
            <div className="flex space-x-2">
              <button
                onClick={handleCreateEntry}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Save Entry
              </button>
              <button
                onClick={() => {
                  setShowNewEntry(false);
                  setNewEntry({ title: '', content: '', mood: 'neutral' });
                }}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'entries' ? (
        <div className="space-y-4">
          {entries.length === 0 ? (
            <div className="text-center py-12">
              <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No journal entries yet</p>
              <p className="text-sm text-gray-400 mt-2">
                Start documenting your trading journey
              </p>
            </div>
          ) : (
            entries.map((entry) => (
              <div key={entry.id} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                      {entry.title}
                      {entry.mood && (
                        <span className="ml-2 text-xl">
                          {moodEmojis[entry.mood] || '😐'}
                        </span>
                      )}
                    </h3>
                    <div className="flex items-center text-sm text-gray-500 mt-1">
                      <Calendar className="w-4 h-4 mr-1" />
                      {formatDate(entry.timestamp || entry.created_at)}
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => console.log('Edit not implemented yet')}
                      className="p-2 text-gray-400 hover:text-gray-600"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteEntry(entry.id)}
                      className="p-2 text-gray-400 hover:text-red-600"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="text-gray-700 whitespace-pre-wrap">{entry.content}</p>
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {tradesWithJournal.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No trades with journal entries</p>
            </div>
          ) : (
            tradesWithJournal.map((trade) => (
              <div key={trade.id} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="mb-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-lg font-semibold">{trade.symbol}</span>
                      <span className={`flex items-center text-sm font-medium ${
                        trade.direction === 'long' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {trade.direction === 'long' ? (
                          <TrendingUp className="w-4 h-4 mr-1" />
                        ) : (
                          <TrendingDown className="w-4 h-4 mr-1" />
                        )}
                        {trade.direction.toUpperCase()}
                      </span>
                    </div>
                    <div className="text-sm text-gray-500">
                      {formatDate(trade.entry_time)}
                    </div>
                  </div>
                  
                  <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Entry:</span>
                      <span className="ml-1 font-medium">${trade.entry_price}</span>
                    </div>
                    {trade.exit_price && (
                      <div>
                        <span className="text-gray-500">Exit:</span>
                        <span className="ml-1 font-medium">${trade.exit_price}</span>
                      </div>
                    )}
                    <div>
                      <span className="text-gray-500">Quantity:</span>
                      <span className="ml-1 font-medium">{trade.quantity}</span>
                    </div>
                    {trade.pnl !== undefined && (
                      <div>
                        <span className="text-gray-500">P&L:</span>
                        <span className={`ml-1 font-medium ${
                          trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          ${trade.pnl.toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                
                {trade.notes && (
                  <div className="mb-4 p-3 bg-gray-50 rounded">
                    <p className="text-sm text-gray-700">{trade.notes}</p>
                  </div>
                )}
                
                {trade.journal_entries.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-sm font-medium text-gray-700">Journal Entries:</h4>
                    {trade.journal_entries.map((entry) => (
                      <div key={entry.id} className="ml-4 p-3 bg-blue-50 rounded">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-sm">{entry.title}</span>
                          <span className="text-xs text-gray-500">
                            {formatDate(entry.timestamp || entry.created_at)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700">{entry.content}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default Journal;