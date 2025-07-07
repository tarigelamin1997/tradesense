
import React, { useState, useEffect } from 'react';
import { Modal } from '../../../components/ui/Modal';
import { reviewsService, TradeReview, TradeReviewCreate, MISTAKE_OPTIONS, MOOD_OPTIONS, formatMistakeTag, formatMoodTag } from '../../../services/reviews';

interface TradeReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  tradeId: string;
  tradeSummary?: {
    symbol: string;
    direction: string;
    pnl?: number;
    result: string;
  };
}

export const TradeReviewModal: React.FC<TradeReviewModalProps> = ({
  isOpen,
  onClose,
  tradeId,
  tradeSummary
}) => {
  const [formData, setFormData] = useState<TradeReviewCreate>({
    quality_score: 3,
    mistakes: [],
    mood: '',
    lesson_learned: '',
    execution_vs_plan: 3
  });
  const [existingReview, setExistingReview] = useState<TradeReview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load existing review when modal opens
  useEffect(() => {
    if (isOpen && tradeId) {
      loadExistingReview();
    }
  }, [isOpen, tradeId]);

  const loadExistingReview = async () => {
    try {
      const review = await reviewsService.getTradeReview(tradeId);
      if (review) {
        setExistingReview(review);
        setFormData({
          quality_score: review.quality_score,
          mistakes: review.mistakes,
          mood: review.mood || '',
          lesson_learned: review.lesson_learned || '',
          execution_vs_plan: review.execution_vs_plan || 3
        });
      }
    } catch (error) {
      console.error('Failed to load existing review:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (existingReview) {
        await reviewsService.updateReview(tradeId, formData);
      } else {
        await reviewsService.createReview(tradeId, formData);
      }
      onClose();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to save review');
    } finally {
      setLoading(false);
    }
  };

  const handleMistakeToggle = (mistake: string) => {
    setFormData(prev => ({
      ...prev,
      mistakes: prev.mistakes.includes(mistake)
        ? prev.mistakes.filter(m => m !== mistake)
        : [...prev.mistakes, mistake]
    }));
  };

  const getQualityScoreColor = (score: number) => {
    if (score >= 4) return 'text-green-600';
    if (score >= 3) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getQualityScoreLabel = (score: number) => {
    const labels = ['', 'Poor', 'Below Average', 'Average', 'Good', 'Excellent'];
    return labels[score] || 'Average';
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Trade Review" size="lg">
      <div className="space-y-6">
        {/* Trade Summary */}
        {tradeSummary && (
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-2">Trade Summary</h3>
            <div className="flex items-center space-x-4 text-sm">
              <span className="font-medium">{tradeSummary.symbol} {tradeSummary.direction}</span>
              <span className={`font-medium ${tradeSummary.pnl && tradeSummary.pnl > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {tradeSummary.result}
              </span>
              {tradeSummary.pnl && (
                <span className={tradeSummary.pnl > 0 ? 'text-green-600' : 'text-red-600'}>
                  ${tradeSummary.pnl.toFixed(2)}
                </span>
              )}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Quality Score */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Trade Quality Score
            </label>
            <div className="space-y-2">
              <input
                type="range"
                min="1"
                max="5"
                value={formData.quality_score}
                onChange={(e) => setFormData(prev => ({ ...prev, quality_score: parseInt(e.target.value) }))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>Poor</span>
                <span>Below Avg</span>
                <span>Average</span>
                <span>Good</span>
                <span>Excellent</span>
              </div>
              <div className={`text-center font-medium ${getQualityScoreColor(formData.quality_score)}`}>
                {formData.quality_score}/5 - {getQualityScoreLabel(formData.quality_score)}
              </div>
            </div>
          </div>

          {/* Execution vs Plan */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Execution vs Plan
            </label>
            <div className="space-y-2">
              <input
                type="range"
                min="1"
                max="5"
                value={formData.execution_vs_plan}
                onChange={(e) => setFormData(prev => ({ ...prev, execution_vs_plan: parseInt(e.target.value) }))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>Way Off</span>
                <span>Poor</span>
                <span>OK</span>
                <span>Good</span>
                <span>Perfect</span>
              </div>
              <div className={`text-center font-medium ${getQualityScoreColor(formData.execution_vs_plan || 3)}`}>
                {formData.execution_vs_plan}/5
              </div>
            </div>
          </div>

          {/* Mistakes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mistakes Made (select all that apply)
            </label>
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
              {MISTAKE_OPTIONS.map(mistake => (
                <label key={mistake} className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={formData.mistakes.includes(mistake)}
                    onChange={() => handleMistakeToggle(mistake)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>{formatMistakeTag(mistake)}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Mood */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Emotional State
            </label>
            <select
              value={formData.mood}
              onChange={(e) => setFormData(prev => ({ ...prev, mood: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select mood...</option>
              {MOOD_OPTIONS.map(mood => (
                <option key={mood} value={mood}>
                  {formatMoodTag(mood)}
                </option>
              ))}
            </select>
          </div>

          {/* Lesson Learned */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Key Lesson Learned
            </label>
            <textarea
              value={formData.lesson_learned}
              onChange={(e) => setFormData(prev => ({ ...prev, lesson_learned: e.target.value }))}
              placeholder="What did you learn from this trade? What will you do differently next time?"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3 pt-6 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Saving...' : existingReview ? 'Update Review' : 'Save Review'}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
};
