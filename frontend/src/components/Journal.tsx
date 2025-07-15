import { useState, useEffect, useMemo } from 'react';
import { journalService, JournalEntry, TradeWithJournal } from '../services/journal';
import { BookOpen, Calendar, Edit, Trash2, Plus, TrendingUp, TrendingDown, AlertCircle, Search, Brain, Activity } from 'lucide-react';
import RichTextEditor from './journal/RichTextEditor';
import JournalTemplates from './journal/JournalTemplates';
import JournalSearch, { SearchFilters } from './journal/JournalSearch';
import MoodTracker, { moodEmojis } from './journal/MoodTracker';
import JournalInsights from './journal/JournalInsights';
import { analyzeSentiment } from '../utils/sentimentAnalyzer';
import { getTrades } from '../services/trades';

function Journal() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [filteredEntries, setFilteredEntries] = useState<JournalEntry[]>([]);
  const [tradesWithJournal, setTradesWithJournal] = useState<TradeWithJournal[]>([]);
  const [allTrades, setAllTrades] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'entries' | 'trades' | 'insights' | 'mood'>('entries');
  const [showNewEntry, setShowNewEntry] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [editingEntry, setEditingEntry] = useState<JournalEntry | null>(null);
  const [newEntry, setNewEntry] = useState({
    title: '',
    content: '',
    mood: 'neutral',
    confidence: 5
  });
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);

  useEffect(() => {
    loadData();
    loadTrades();
  }, [activeTab]);

  useEffect(() => {
    setFilteredEntries(entries);
  }, [entries]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (activeTab === 'entries' || activeTab === 'insights' || activeTab === 'mood') {
        const data = await journalService.getJournalEntries();
        setEntries(data);
      } else if (activeTab === 'trades') {
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

  const loadTrades = async () => {
    try {
      const trades = await getTrades();
      setAllTrades(trades);
    } catch (err) {
      console.error('Failed to load trades:', err);
    }
  };

  const handleCreateEntry = async () => {
    if (!newEntry.title || !newEntry.content) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      // Analyze sentiment of the content
      const sentiment = analyzeSentiment(newEntry.content);
      
      const entryData = {
        ...newEntry,
        sentiment: sentiment.sentiment,
        sentimentScore: sentiment.score
      };
      
      if (editingEntry) {
        await journalService.updateJournalEntry(editingEntry.id, entryData);
      } else {
        await journalService.createJournalEntry(entryData);
      }
      
      setShowNewEntry(false);
      setEditingEntry(null);
      setNewEntry({ title: '', content: '', mood: 'neutral', confidence: 5 });
      setSelectedTemplate(null);
      loadData();
    } catch (err: any) {
      alert('Failed to save journal entry: ' + err.message);
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

  const handleEditEntry = (entry: JournalEntry) => {
    setEditingEntry(entry);
    setNewEntry({
      title: entry.title,
      content: entry.content,
      mood: entry.mood || 'neutral',
      confidence: 5 // Default since we don't store this yet
    });
    setShowNewEntry(true);
  };

  const handleSearch = (results: JournalEntry[], filters: SearchFilters) => {
    setFilteredEntries(results);
  };

  const handleTemplateSelect = (template: any) => {
    setSelectedTemplate(template);
    setNewEntry({
      ...newEntry,
      title: template.name,
      content: template.content
    });
    setShowNewEntry(true);
  };

  const handleMoodSelect = (mood: string, confidence: number) => {
    setNewEntry(prev => ({
      ...prev,
      mood,
      confidence
    }));
  };

  // Prepare mood data for the mood tracker
  const moodData = useMemo(() => {
    return entries.map(entry => {
      const relatedTrades = allTrades.filter(trade => {
        const tradeDate = new Date(trade.exit_time || trade.entry_time).toDateString();
        const entryDate = new Date(entry.created_at).toDateString();
        return tradeDate === entryDate;
      });
      
      const dayPnl = relatedTrades.reduce((sum, trade) => sum + (trade.pnl || 0), 0);
      const winRate = relatedTrades.length > 0 
        ? (relatedTrades.filter(t => t.pnl > 0).length / relatedTrades.length) * 100
        : 0;
      
      return {
        date: entry.created_at,
        mood: entry.mood || 'neutral',
        confidence: 5, // Default since we don't store this yet
        pnl: dayPnl,
        winRate,
        tradeCount: relatedTrades.length
      };
    });
  }, [entries, allTrades]);

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
          <div className="flex space-x-2">
            <button
              onClick={() => setShowSearch(!showSearch)}
              className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              <Search className="w-4 h-4 mr-1" />
              Search
            </button>
            <button
              onClick={() => {
                setEditingEntry(null);
                setNewEntry({ title: '', content: '', mood: 'neutral', confidence: 5 });
                setShowNewEntry(!showNewEntry);
              }}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-1" />
              New Entry
            </button>
          </div>
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
          <button
            onClick={() => setActiveTab('insights')}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'insights'
                ? 'text-blue-600 border-blue-600'
                : 'text-gray-500 border-transparent hover:text-gray-700'
            }`}
          >
            <Brain className="inline w-4 h-4 mr-1" />
            Insights
          </button>
          <button
            onClick={() => setActiveTab('mood')}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'mood'
                ? 'text-blue-600 border-blue-600'
                : 'text-gray-500 border-transparent hover:text-gray-700'
            }`}
          >
            <Activity className="inline w-4 h-4 mr-1" />
            Mood Analysis
          </button>
        </div>
      </div>

      {showNewEntry && (
        <div className="mb-6 p-6 bg-gray-50 rounded-lg">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">
              {editingEntry ? 'Edit Journal Entry' : 'New Journal Entry'}
            </h3>
            <JournalTemplates 
              onSelectTemplate={handleTemplateSelect}
              tradeData={allTrades.length > 0 ? allTrades[0] : undefined}
            />
          </div>
          
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
            
            {/* Mood and Confidence Selector */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mood
                </label>
                <select
                  value={newEntry.mood}
                  onChange={(e) => setNewEntry({ ...newEntry, mood: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                  Confidence: {newEntry.confidence}/10
                </label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={newEntry.confidence}
                  onChange={(e) => setNewEntry({ ...newEntry, confidence: parseInt(e.target.value) })}
                  className="w-full mt-2"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Content
              </label>
              <RichTextEditor
                value={newEntry.content}
                onChange={(content) => setNewEntry({ ...newEntry, content })}
                placeholder="What happened in the markets today?"
                height={300}
                availableTrades={allTrades.map(t => ({
                  id: t.id,
                  symbol: t.symbol,
                  date: new Date(t.entry_time).toLocaleDateString()
                }))}
                onTradeMention={(tradeId) => {
                  console.log('Trade mentioned:', tradeId);
                }}
              />
            </div>
            
            <div className="flex space-x-2">
              <button
                onClick={handleCreateEntry}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                {editingEntry ? 'Update Entry' : 'Save Entry'}
              </button>
              <button
                onClick={() => {
                  setShowNewEntry(false);
                  setEditingEntry(null);
                  setNewEntry({ title: '', content: '', mood: 'neutral', confidence: 5 });
                  setSelectedTemplate(null);
                }}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Search Component */}
      {showSearch && (
        <div className="mb-6">
          <JournalSearch 
            entries={entries}
            onSearch={handleSearch}
            onClose={() => setShowSearch(false)}
          />
        </div>
      )}

      {activeTab === 'entries' ? (
        <div className="space-y-4">
          {filteredEntries.length === 0 ? (
            <div className="text-center py-12">
              <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No journal entries found</p>
              <p className="text-sm text-gray-400 mt-2">
                {entries.length > 0 ? 'Try adjusting your search filters' : 'Start documenting your trading journey'}
              </p>
            </div>
          ) : (
            filteredEntries.map((entry) => (
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
                      onClick={() => handleEditEntry(entry)}
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
                <div 
                  className="prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{ __html: entry.content }}
                />
              </div>
            ))
          )}
        </div>
      ) : activeTab === 'trades' ? (
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
      ) : activeTab === 'insights' ? (
        <div>
          <JournalInsights 
            entries={entries}
            trades={allTrades}
            onInsightClick={(insight) => {
              console.log('Insight clicked:', insight);
            }}
          />
        </div>
      ) : activeTab === 'mood' ? (
        <div>
          <MoodTracker 
            moodData={moodData}
            onMoodSelect={handleMoodSelect}
            currentMood={newEntry.mood}
            currentConfidence={newEntry.confidence}
          />
        </div>
      ) : null}
    </div>
  );
}

export default Journal;