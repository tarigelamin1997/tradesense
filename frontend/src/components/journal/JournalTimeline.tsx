import React, { useState, useEffect } from 'react';
import { journalService, JournalEntry, JournalEntryCreate, JournalEntryUpdate } from '../../services/journal';

interface EmotionData {
  emotion?: 'Calm' | 'Excited' | 'Anxious' | 'Fearful' | 'Angry' | 'Confident' | 'Frustrated' | 'Euphoric' | 'Neutral';
  confidence_score?: number;
  mental_triggers?: ('FOMO' | 'Hesitation' | 'Overconfidence' | 'Revenge' | 'Fear' | 'Greed' | 'Impatience' | 'Perfectionism' | 'Desperation')[];
}

interface JournalEntry {
  id: string;
  trade_id?: string;
  title: string;
  content: string;
  mood?: string;
  emotion_data?: EmotionData;
  timestamp: string;
  created_at: string;
  updated_at: string;
}

interface JournalEntryCreateRequest {
  title: string;
  content: string;
  mood?: string;
  emotion_data?: EmotionData;
}

interface JournalEntryUpdateRequest {
  title: string;
  content: string;
  mood?: string;
  emotion_data?: EmotionData;
}

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

interface JournalEntryFormData {
  title: string;
  content: string;
  mood?: string;
  emotion_data?: EmotionData;
}

const JournalEntryForm: React.FC<JournalEntryFormProps> = ({
  initialData,
  onSubmit,
  onCancel
}) => {
  const [title, setTitle] = useState(initialData?.title || '');
  const [content, setContent] = useState(initialData?.content || '');
  const [mood, setMood] = useState(initialData?.mood || '');
  const [emotion, setEmotion] = useState<EmotionData['emotion']>(initialData?.emotion_data?.emotion || undefined);
  const [confidence, setConfidence] = useState<number | undefined>(initialData?.emotion_data?.confidence_score || undefined);
  const [triggers, setTriggers] = useState<EmotionData['mental_triggers']>(initialData?.emotion_data?.mental_triggers || undefined);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;

    const emotionData = emotion || confidence || triggers ? {
      emotion,
      confidence_score: confidence,
      mental_triggers: triggers,
    } : undefined;

    onSubmit({ 
      title: title.trim(), 
      content: content.trim(), 
      mood: mood || undefined,
      emotion_data: emotionData,
     });
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
    <form onSubmit={handleSubmit} className="space-y-6 p-4 bg-gray-50 rounded-lg">
      <div>
        <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
          Title
        </label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded-md"
          placeholder="Entry title..."
          required
        />
      </div>

      <div>
        <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-1">
          Content
        </label>
        <textarea
          id="content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={4}
          className="w-full p-2 border border-gray-300 rounded-md"
          placeholder="What happened? How did you feel?"
          required
        />
      </div>

      <div>
        <label htmlFor="mood" className="block text-sm font-medium text-gray-700 mb-1">
          Mood
        </label>
        <select
          id="mood"
          value={mood}
          onChange={(e) => setMood(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded-md"
        >
          {moodOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Psychology Tracking Section */}
      <div className="space-y-4 p-4 bg-white rounded-lg border">
        <h4 className="text-sm font-semibold text-gray-800 mb-3">🧠 Psychology Tracker</h4>

        <EmotionSelector value={emotion} onChange={setEmotion} />
        <ConfidenceSlider value={confidence} onChange={setConfidence} />
        <TriggerSelector value={triggers || []} onChange={setTriggers} />
      </div>

      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          {initialData ? 'Update' : 'Add'} Entry
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

  const getEmotionEmoji = (emotion?: string) => {
    const emotionMap: Record<string, string> = {
      Calm: '😌',
      Excited: '🚀',
      Anxious: '😰',
      Fearful: '😨',
      Angry: '😡',
      Confident: '😎',
      Frustrated: '😤',
      Euphoric: '🤩',
      Neutral: '😐',
    };
    return emotion ? emotionMap[emotion] || '💭' : '💭';
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-gray-800">{entry.title}</h3>
        <div className="flex gap-2">
          <button
            onClick={onEdit}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            Edit
          </button>
          <button
            onClick={onDelete}
            className="text-red-600 hover:text-red-800 text-sm"
          >
            Delete
          </button>
        </div>
      </div>

      <p className="text-gray-600 mb-3">{entry.content}</p>

      {/* Psychology Data Display */}
      {entry.emotion_data && (
        <div className="bg-gray-50 rounded-lg p-3 mb-3 space-y-2">
          <div className="text-xs font-semibold text-gray-700">🧠 Psychology Data</div>

          {entry.emotion_data.emotion && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-lg">{getEmotionEmoji(entry.emotion_data.emotion)}</span>
              <span className="text-gray-700">Feeling: {entry.emotion_data.emotion}</span>
            </div>
          )}

          {entry.emotion_data.confidence_score && (
            <div className="flex items-center gap-2 text-sm">
              <span>🎯</span>
              <span className="text-gray-700">Confidence: {entry.emotion_data.confidence_score}/10</span>
            </div>
          )}

          {entry.emotion_data.mental_triggers && entry.emotion_data.mental_triggers.length > 0 && (
            <div className="flex items-center gap-2 text-sm">
              <span>⚠️</span>
              <span className="text-gray-700">Triggers: </span>
              <div className="flex flex-wrap gap-1">
                {entry.emotion_data.mental_triggers.map((trigger, index) => (
                  <span 
                    key={index}
                    className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full"
                  >
                    {trigger}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="flex justify-between items-center text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <span>{formatDate(entry.timestamp)}</span>
          {entry.mood && (
            <span className="flex items-center gap-1">
              {getMoodEmoji(entry.mood)} {entry.mood}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

// EmotionSelector Component
interface EmotionSelectorProps {
  value?: EmotionData['emotion'];
  onChange: (emotion: EmotionData['emotion']) => void;
}

const EmotionSelector: React.FC<EmotionSelectorProps> = ({ value, onChange }) => {
  const emotionOptions: EmotionData['emotion'][] = [
    'Calm', 'Excited', 'Anxious', 'Fearful', 'Angry', 'Confident', 'Frustrated', 'Euphoric', 'Neutral',
  ];

  return (
    <div>
      <label htmlFor="emotion" className="block text-sm font-medium text-gray-700 mb-1">
        Emotion
      </label>
      <select
        id="emotion"
        value={value || ''}
        onChange={(e) => onChange(e.target.value as EmotionData['emotion'])}
        className="w-full p-2 border border-gray-300 rounded-md"
      >
        <option value="">Select Emotion</option>
        {emotionOptions.map((emotion) => (
          <option key={emotion} value={emotion}>
            {emotion}
          </option>
        ))}
      </select>
    </div>
  );
};

// ConfidenceSlider Component
interface ConfidenceSliderProps {
  value?: number;
  onChange: (confidence: number) => void;
}

const ConfidenceSlider: React.FC<ConfidenceSliderProps> = ({ value, onChange }) => {
  return (
    <div>
      <label htmlFor="confidence" className="block text-sm font-medium text-gray-700 mb-1">
        Confidence (1-10)
      </label>
      <input
        type="range"
        id="confidence"
        min="1"
        max="10"
        value={value || 5}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full"
      />
      <p className="text-sm text-gray-500 mt-1">Confidence Level: {value || 5}</p>
    </div>
  );
};

// TriggerSelector Component
interface TriggerSelectorProps {
  value: EmotionData['mental_triggers'];
  onChange: (triggers: EmotionData['mental_triggers']) => void;
}

const TriggerSelector: React.FC<TriggerSelectorProps> = ({ value, onChange }) => {
  const triggerOptions: NonNullable<EmotionData['mental_triggers']> = [
    'FOMO', 'Hesitation', 'Overconfidence', 'Revenge', 'Fear', 'Greed', 'Impatience', 'Perfectionism', 'Desperation',
  ];

  const handleTriggerChange = (trigger: string) => {
    if (value && value.includes(trigger as any)) {
      onChange(value.filter((t) => t !== trigger) as any);
    } else {
      onChange([...(value || []), trigger] as any);
    }
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Mental Triggers
      </label>
      <div className="flex flex-wrap gap-2">
        {triggerOptions.map((trigger) => (
          <label key={trigger} className="inline-flex items-center">
            <input
              type="checkbox"
              className="form-checkbox h-5 w-5 text-blue-600"
              value={trigger}
              checked={value?.includes(trigger as any) || false}
              onChange={() => handleTriggerChange(trigger)}
            />
            <span className="ml-2 text-gray-700">{trigger}</span>
          </label>
        ))}
      </div>
    </div>
  );
};