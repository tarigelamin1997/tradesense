
import React, { useState, useEffect } from 'react';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { Modal } from '../../../components/ui/Modal';
import { mentalMapService, TimelineEvent, SessionTimeline } from '../../../services/mentalMap';

interface MentalMapTimelineProps {
  sessionId: string;
}

const moodColors = {
  calm: 'bg-green-100 text-green-800',
  focused: 'bg-blue-100 text-blue-800',
  confident: 'bg-purple-100 text-purple-800',
  anxious: 'bg-yellow-100 text-yellow-800',
  revenge: 'bg-red-100 text-red-800',
  fearful: 'bg-orange-100 text-orange-800',
  frustrated: 'bg-pink-100 text-pink-800',
  euphoric: 'bg-indigo-100 text-indigo-800',
  overconfident: 'bg-red-200 text-red-900',
  uncertain: 'bg-gray-100 text-gray-800'
};

const moodOptions = [
  'calm', 'focused', 'confident', 'anxious', 'revenge', 
  'fearful', 'frustrated', 'euphoric', 'overconfident', 'uncertain'
];

const ruleBreakOptions = [
  'broke entry rule', 'broke exit rule', 'overleveraged', 'fomo', 
  'revenge trading', 'overconfidence', 'hesitation', 'ignored stop loss',
  'chased price', 'emotional trading', 'ignored risk management'
];

export const MentalMapTimeline: React.FC<MentalMapTimelineProps> = ({ sessionId }) => {
  const [timeline, setTimeline] = useState<SessionTimeline | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedTimestamp, setSelectedTimestamp] = useState<string>('');
  const [replayPosition, setReplayPosition] = useState(0);

  // Form state for adding mental entry
  const [newEntry, setNewEntry] = useState({
    note: '',
    mood: 'calm',
    confidence_score: '',
    checklist_flags: [] as string[],
    chart_context: ''
  });

  useEffect(() => {
    loadTimeline();
  }, [sessionId]);

  const loadTimeline = async () => {
    try {
      setLoading(true);
      const data = await mentalMapService.getSessionTimeline(sessionId);
      setTimeline(data);
    } catch (err) {
      setError('Failed to load session timeline');
      console.error('Timeline load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddMentalEntry = async () => {
    if (!newEntry.note.trim()) return;

    try {
      await mentalMapService.createMentalEntry({
        session_id: sessionId,
        timestamp: selectedTimestamp || new Date().toISOString(),
        note: newEntry.note,
        mood: newEntry.mood,
        confidence_score: newEntry.confidence_score,
        checklist_flags: newEntry.checklist_flags,
        chart_context: newEntry.chart_context
      });

      setNewEntry({
        note: '',
        mood: 'calm',
        confidence_score: '',
        checklist_flags: [],
        chart_context: ''
      });
      setShowAddModal(false);
      loadTimeline();
    } catch (err) {
      console.error('Failed to add mental entry:', err);
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const handleReplaySlider = (position: number) => {
    setReplayPosition(position);
  };

  const getFilteredTimeline = () => {
    if (!timeline) return [];
    
    // Filter timeline based on replay position
    const totalEvents = timeline.timeline.length;
    const visibleEvents = Math.floor((replayPosition / 100) * totalEvents);
    return timeline.timeline.slice(0, visibleEvents);
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center text-red-600">
          <p>{error}</p>
          <Button onClick={loadTimeline} className="mt-4">
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  if (!timeline) {
    return (
      <Card className="p-6">
        <div className="text-center text-gray-500">
          <p>No timeline data available</p>
        </div>
      </Card>
    );
  }

  const filteredTimeline = getFilteredTimeline();

  return (
    <div className="space-y-6">
      {/* Session Header */}
      <Card className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {timeline.session.session_name || 'Trading Session'}
            </h2>
            <p className="text-gray-600">
              {formatDate(timeline.session.start_time)} • {timeline.session.total_trades} trades
            </p>
          </div>
          <div className="flex space-x-2">
            <Button 
              onClick={() => {
                setSelectedTimestamp(new Date().toISOString());
                setShowAddModal(true);
              }}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Add Mental Note
            </Button>
          </div>
        </div>

        {timeline.session.market_conditions && (
          <div className="mb-4">
            <span className="text-sm font-medium text-gray-700">Market Conditions: </span>
            <span className="text-sm text-gray-600">{timeline.session.market_conditions}</span>
          </div>
        )}

        {timeline.session.dominant_mood && (
          <div className="mb-4">
            <span className="text-sm font-medium text-gray-700">Dominant Mood: </span>
            <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
              moodColors[timeline.session.dominant_mood as keyof typeof moodColors] || 'bg-gray-100 text-gray-800'
            }`}>
              {timeline.session.dominant_mood}
            </span>
          </div>
        )}

        {/* Replay Slider */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Session Replay ({Math.floor((replayPosition / 100) * timeline.timeline.length)} / {timeline.timeline.length} events)
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={replayPosition}
            onChange={(e) => handleReplaySlider(Number(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
        </div>
      </Card>

      {/* Timeline */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Session Timeline</h3>
        
        {filteredTimeline.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No events to display</p>
        ) : (
          <div className="space-y-4">
            {filteredTimeline.map((event, index) => (
              <div key={index} className="flex items-start space-x-4 p-4 rounded-lg bg-gray-50">
                <div className="flex-shrink-0">
                  <div className={`w-3 h-3 rounded-full ${
                    event.type === 'trade' ? 'bg-blue-500' : 'bg-green-500'
                  }`}></div>
                </div>
                
                <div className="flex-grow">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-900">
                      {formatTime(event.timestamp)}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      event.type === 'trade' 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {event.type === 'trade' ? 'Trade' : 'Mental Note'}
                    </span>
                  </div>

                  {event.type === 'trade' ? (
                    <div className="space-y-1">
                      <p className="text-sm font-medium">
                        {event.data.direction.toUpperCase()} {event.data.quantity} {event.data.symbol} @ ${event.data.entry_price}
                      </p>
                      {event.data.exit_price && (
                        <p className="text-sm text-gray-600">
                          Exit: ${event.data.exit_price} • P&L: 
                          <span className={`ml-1 ${
                            event.data.pnl > 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            ${event.data.pnl?.toFixed(2)}
                          </span>
                        </p>
                      )}
                      {event.data.strategy_tag && (
                        <p className="text-sm text-gray-600">Strategy: {event.data.strategy_tag}</p>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                          moodColors[event.data.mood as keyof typeof moodColors] || 'bg-gray-100 text-gray-800'
                        }`}>
                          {event.data.mood}
                        </span>
                        {event.data.confidence_score && (
                          <span className="text-xs text-gray-600">
                            Confidence: {event.data.confidence_score}/10
                          </span>
                        )}
                      </div>
                      
                      <p className="text-sm text-gray-800">{event.data.note}</p>
                      
                      {event.data.checklist_flags && event.data.checklist_flags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {event.data.checklist_flags.map((flag: string, flagIndex: number) => (
                            <span key={flagIndex} className="inline-flex px-2 py-1 rounded-full text-xs bg-red-100 text-red-800">
                              {flag}
                            </span>
                          ))}
                        </div>
                      )}
                      
                      {event.data.chart_context && (
                        <p className="text-xs text-gray-600 italic">{event.data.chart_context}</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Add Mental Entry Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="Add Mental Note"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Note *
            </label>
            <textarea
              value={newEntry.note}
              onChange={(e) => setNewEntry({ ...newEntry, note: e.target.value })}
              placeholder="What were you thinking or feeling?"
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mood
            </label>
            <select
              value={newEntry.mood}
              onChange={(e) => setNewEntry({ ...newEntry, mood: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {moodOptions.map(mood => (
                <option key={mood} value={mood}>{mood}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confidence Score (1-10)
            </label>
            <Input
              type="number"
              min="1"
              max="10"
              value={newEntry.confidence_score}
              onChange={(e) => setNewEntry({ ...newEntry, confidence_score: e.target.value })}
              placeholder="How confident were you?"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Rule Breaks / Flags
            </label>
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {ruleBreakOptions.map(flag => (
                <label key={flag} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={newEntry.checklist_flags.includes(flag)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setNewEntry({
                          ...newEntry,
                          checklist_flags: [...newEntry.checklist_flags, flag]
                        });
                      } else {
                        setNewEntry({
                          ...newEntry,
                          checklist_flags: newEntry.checklist_flags.filter(f => f !== flag)
                        });
                      }
                    }}
                    className="mr-2"
                  />
                  <span className="text-sm">{flag}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Chart Context
            </label>
            <Input
              value={newEntry.chart_context}
              onChange={(e) => setNewEntry({ ...newEntry, chart_context: e.target.value })}
              placeholder="Market setup, support/resistance levels, etc."
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <Button
              onClick={() => setShowAddModal(false)}
              variant="outline"
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddMentalEntry}
              disabled={!newEntry.note.trim()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Add Note
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
