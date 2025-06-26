
import React, { useState, useEffect } from 'react';
import { DailyTimelineData, DailyReflection, timelineService } from '../../../services/timeline';

interface DailyDiaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  dayData: DailyTimelineData;
}

export const DailyDiaryModal: React.FC<DailyDiaryModalProps> = ({
  isOpen,
  onClose,
  dayData
}) => {
  const [reflection, setReflection] = useState<DailyReflection>({
    reflection_date: dayData.date,
    mood_score: dayData.mood_score || 0,
    summary: dayData.reflection_summary || '',
    dominant_emotion: dayData.dominant_emotion || ''
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadReflection();
    }
  }, [isOpen, dayData.date]);

  const loadReflection = async () => {
    try {
      const existingReflection = await timelineService.getDailyReflection(dayData.date);
      if (existingReflection) {
        setReflection(existingReflection);
      }
    } catch (error) {
      console.error('Failed to load reflection:', error);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await timelineService.saveDailyReflection(reflection);
      onClose();
    } catch (error) {
      console.error('Failed to save reflection:', error);
      alert('Failed to save reflection. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const getMoodEmoji = (score: number) => {
    if (score >= 4) return '🤩';
    if (score >= 2) return '😊';
    if (score >= 0) return '😐';
    if (score >= -2) return '😔';
    return '😭';
  };

  const getMoodLabel = (score: number) => {
    if (score >= 4) return 'Excellent';
    if (score >= 2) return 'Good';
    if (score >= 0) return 'Neutral';
    if (score >= -2) return 'Poor';
    return 'Terrible';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">
              Trading Diary - {new Date(dayData.date).toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>
          </div>

          {/* Trading Summary */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold mb-3">Trading Summary</h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold">
                  {dayData.trade_count}
                </div>
                <div className="text-sm text-gray-600">Trades</div>
              </div>
              <div>
                <div className={`text-2xl font-bold ${dayData.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {dayData.pnl >= 0 ? '+' : ''}${dayData.pnl.toFixed(2)}
                </div>
                <div className="text-sm text-gray-600">P&L</div>
              </div>
              <div>
                <div className="text-2xl">
                  {dayData.emotion_emoji || '😐'}
                </div>
                <div className="text-sm text-gray-600 capitalize">
                  {dayData.dominant_emotion || 'No emotion'}
                </div>
              </div>
            </div>
          </div>

          {/* Trade List */}
          {dayData.trades.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold mb-3">Trades</h3>
              <div className="space-y-2">
                {dayData.trades.map((trade) => (
                  <div key={trade.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <div>
                      <span className="font-medium">{trade.symbol}</span>
                      {trade.strategy && (
                        <span className="ml-2 text-sm text-gray-600">({trade.strategy})</span>
                      )}
                    </div>
                    <div className={`font-semibold ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {trade.pnl >= 0 ? '+' : ''}${trade.pnl?.toFixed(2) || '0.00'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Mood Slider */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Overall Mood: {getMoodEmoji(reflection.mood_score || 0)} {getMoodLabel(reflection.mood_score || 0)}
            </label>
            <input
              type="range"
              min="-5"
              max="5"
              step="1"
              value={reflection.mood_score || 0}
              onChange={(e) => setReflection({
                ...reflection,
                mood_score: parseInt(e.target.value)
              })}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Terrible</span>
              <span>Neutral</span>
              <span>Excellent</span>
            </div>
          </div>

          {/* Emotion Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dominant Emotion
            </label>
            <select
              value={reflection.dominant_emotion || ''}
              onChange={(e) => setReflection({
                ...reflection,
                dominant_emotion: e.target.value
              })}
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              <option value="">Select emotion...</option>
              <option value="confident">Confident 😎</option>
              <option value="anxious">Anxious 😰</option>
              <option value="calm">Calm 😌</option>
              <option value="frustrated">Frustrated 😤</option>
              <option value="excited">Excited 🤩</option>
              <option value="fearful">Fearful 😨</option>
              <option value="focused">Focused 🎯</option>
              <option value="overwhelmed">Overwhelmed 😵</option>
              <option value="disciplined">Disciplined 🧘</option>
              <option value="impulsive">Impulsive 🤪</option>
            </select>
          </div>

          {/* Summary Notes */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Daily Reflection
            </label>
            <textarea
              value={reflection.summary || ''}
              onChange={(e) => setReflection({
                ...reflection,
                summary: e.target.value
              })}
              placeholder="What went well today? What would you do differently? Any insights about your trading decisions?"
              rows={4}
              className="w-full p-3 border border-gray-300 rounded-md resize-none"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Reflection'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
