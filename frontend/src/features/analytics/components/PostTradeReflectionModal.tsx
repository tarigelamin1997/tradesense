
import React, { useState, useEffect } from 'react';
import emotionsService from '../../../services/emotions';

interface PostTradeReflectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  tradeId: string;
  existingReflection?: {
    emotional_tags?: string[];
    reflection_notes?: string;
    emotional_score?: number;
    executed_plan?: boolean;
    post_trade_mood?: string;
  };
}

const PostTradeReflectionModal: React.FC<PostTradeReflectionModalProps> = ({
  isOpen,
  onClose,
  tradeId,
  existingReflection
}) => {
  const [emotionalStates, setEmotionalStates] = useState<string[]>([]);
  const [moodCategories, setMoodCategories] = useState<string[]>([]);
  const [selectedEmotions, setSelectedEmotions] = useState<string[]>([]);
  const [reflectionNotes, setReflectionNotes] = useState('');
  const [emotionalScore, setEmotionalScore] = useState(5);
  const [executedPlan, setExecutedPlan] = useState<boolean | null>(null);
  const [postTradeMood, setPostTradeMood] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const loadEmotionalStates = async () => {
      try {
        const data = await emotionsService.getEmotionalStates();
        setEmotionalStates(data.emotional_states);
        setMoodCategories(data.mood_categories);
      } catch (error) {
        console.error('Failed to load emotional states:', error);
      }
    };

    if (isOpen) {
      loadEmotionalStates();
      
      // Pre-populate with existing data
      if (existingReflection) {
        setSelectedEmotions(existingReflection.emotional_tags || []);
        setReflectionNotes(existingReflection.reflection_notes || '');
        setEmotionalScore(existingReflection.emotional_score || 5);
        setExecutedPlan(existingReflection.executed_plan || null);
        setPostTradeMood(existingReflection.post_trade_mood || '');
      }
    }
  }, [isOpen, existingReflection]);

  const handleEmotionToggle = (emotion: string) => {
    setSelectedEmotions(prev => 
      prev.includes(emotion) 
        ? prev.filter(e => e !== emotion)
        : [...prev, emotion]
    );
  };

  const handleSubmit = async () => {
    if (!executedPlan === null || selectedEmotions.length === 0) {
      alert('Please select at least one emotion and indicate if you followed your plan.');
      return;
    }

    setIsSubmitting(true);
    try {
      await emotionsService.updateTradeReflection({
        trade_id: tradeId,
        emotional_tags: selectedEmotions,
        reflection_notes: reflectionNotes,
        emotional_score: emotionalScore,
        executed_plan: executedPlan!,
        post_trade_mood: postTradeMood
      });
      
      onClose();
      // Refresh trade data if needed
    } catch (error) {
      console.error('Failed to save reflection:', error);
      alert('Failed to save reflection. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Post-Trade Reflection</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Emotional States Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            How were you feeling during this trade? (Select all that apply)
          </label>
          <div className="grid grid-cols-3 gap-2">
            {emotionalStates.map((emotion) => (
              <button
                key={emotion}
                onClick={() => handleEmotionToggle(emotion)}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  selectedEmotions.includes(emotion)
                    ? 'bg-blue-100 text-blue-800 border-2 border-blue-300'
                    : 'bg-gray-100 text-gray-700 border-2 border-transparent hover:bg-gray-200'
                }`}
              >
                {emotion}
              </button>
            ))}
          </div>
        </div>

        {/* Emotional Control Score */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            How emotionally controlled were you? (1 = Completely emotional, 10 = Perfectly controlled)
          </label>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">1</span>
            <input
              type="range"
              min="1"
              max="10"
              value={emotionalScore}
              onChange={(e) => setEmotionalScore(parseInt(e.target.value))}
              className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <span className="text-sm text-gray-500">10</span>
            <span className="text-lg font-semibold text-blue-600 ml-2">
              {emotionalScore}
            </span>
          </div>
        </div>

        {/* Plan Execution */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Did you follow your trading plan?
          </label>
          <div className="flex space-x-4">
            <button
              onClick={() => setExecutedPlan(true)}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                executedPlan === true
                  ? 'bg-green-100 text-green-800 border-2 border-green-300'
                  : 'bg-gray-100 text-gray-700 border-2 border-transparent hover:bg-gray-200'
              }`}
            >
              ✅ Yes, I followed my plan
            </button>
            <button
              onClick={() => setExecutedPlan(false)}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                executedPlan === false
                  ? 'bg-red-100 text-red-800 border-2 border-red-300'
                  : 'bg-gray-100 text-gray-700 border-2 border-transparent hover:bg-gray-200'
              }`}
            >
              ❌ No, I deviated from my plan
            </button>
          </div>
        </div>

        {/* Post-Trade Mood */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            How do you feel about this trade now?
          </label>
          <select
            value={postTradeMood}
            onChange={(e) => setPostTradeMood(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select mood...</option>
            {moodCategories.map((mood) => (
              <option key={mood} value={mood}>
                {mood}
              </option>
            ))}
          </select>
        </div>

        {/* Reflection Notes */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Write your reflection (What did you learn? What would you do differently?)
          </label>
          <textarea
            value={reflectionNotes}
            onChange={(e) => setReflectionNotes(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Example: I should have waited for better confirmation before entering. I let FOMO drive my decision..."
            maxLength={2000}
          />
          <div className="text-right text-sm text-gray-500 mt-1">
            {reflectionNotes.length}/2000 characters
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-4">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || selectedEmotions.length === 0 || executedPlan === null}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? 'Saving...' : 'Save Reflection'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PostTradeReflectionModal;
