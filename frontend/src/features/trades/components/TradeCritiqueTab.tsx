
import React, { useState, useEffect } from 'react';
import { critiqueService, CritiqueData, CritiqueFeedback } from '../../../services/critique';

interface TradeCritiqueTabProps {
  tradeId: string;
}

const TradeCritiqueTab: React.FC<TradeCritiqueTabProps> = ({ tradeId }) => {
  const [critique, setCritique] = useState<CritiqueData | null>(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCritique();
  }, [tradeId]);

  const loadCritique = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await critiqueService.getTradeCritique(tradeId);
      setCritique(data);
    } catch (err) {
      setError('Failed to load critique');
      console.error('Error loading critique:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    try {
      setRegenerating(true);
      const data = await critiqueService.regenerateCritique(tradeId);
      setCritique(data);
      setFeedbackSubmitted(false); // Reset feedback state
    } catch (err) {
      setError('Failed to regenerate critique');
      console.error('Error regenerating critique:', err);
    } finally {
      setRegenerating(false);
    }
  };

  const handleFeedback = async (helpful: boolean, rating?: number) => {
    try {
      const feedback: CritiqueFeedback = { helpful, rating };
      await critiqueService.submitFeedback(tradeId, feedback);
      setFeedbackSubmitted(true);
    } catch (err) {
      console.error('Error submitting feedback:', err);
    }
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 8) return 'text-green-600';
    if (confidence >= 6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getTagColor = (tag: string): string => {
    const negativePatterns = ['overconfidence', 'fomo', 'revenge', 'panic', 'poor_execution'];
    const positivePatterns = ['excellent_execution', 'disciplined', 'profitable', 'good_execution'];
    
    if (negativePatterns.some(pattern => tag.includes(pattern))) {
      return 'bg-red-100 text-red-800';
    }
    if (positivePatterns.some(pattern => tag.includes(pattern))) {
      return 'bg-green-100 text-green-800';
    }
    return 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-2 text-gray-600">Generating AI critique...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={loadCritique}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!critique) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-600">No critique available</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header with confidence score */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <h3 className="text-lg font-semibold">AI Trade Critique</h3>
          <span className={`text-lg font-bold ${getConfidenceColor(critique.confidence)}`}>
            Confidence: {critique.confidence}/10
          </span>
        </div>
        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50"
        >
          {regenerating ? 'Regenerating...' : 'Regenerate'}
        </button>
      </div>

      {/* Summary */}
      <div className="bg-blue-50 p-4 rounded-lg">
        <h4 className="font-semibold text-blue-900 mb-2">Summary</h4>
        <p className="text-blue-800">{critique.summary}</p>
      </div>

      {/* Suggestion */}
      <div className="bg-green-50 p-4 rounded-lg">
        <h4 className="font-semibold text-green-900 mb-2">Suggestions</h4>
        <p className="text-green-800">{critique.suggestion}</p>
      </div>

      {/* Tags */}
      {critique.tags.length > 0 && (
        <div>
          <h4 className="font-semibold mb-2">Analysis Tags</h4>
          <div className="flex flex-wrap gap-2">
            {critique.tags.map((tag, index) => (
              <span
                key={index}
                className={`px-3 py-1 rounded-full text-sm font-medium ${getTagColor(tag)}`}
              >
                {tag.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Detailed Analysis */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold mb-2">Technical Analysis</h4>
          <p className="text-sm text-gray-700">{critique.technical_analysis}</p>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold mb-2">Psychological Analysis</h4>
          <p className="text-sm text-gray-700">{critique.psychological_analysis}</p>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold mb-2">Risk Assessment</h4>
          <p className="text-sm text-gray-700">{critique.risk_assessment}</p>
        </div>
      </div>

      {/* Feedback Section */}
      {!feedbackSubmitted ? (
        <div className="border-t pt-4">
          <h4 className="font-semibold mb-3">Was this critique helpful?</h4>
          <div className="flex space-x-4">
            <button
              onClick={() => handleFeedback(true, 5)}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              👍 Yes, helpful
            </button>
            <button
              onClick={() => handleFeedback(false, 2)}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
              👎 Not helpful
            </button>
          </div>
        </div>
      ) : (
        <div className="border-t pt-4">
          <p className="text-green-600 font-medium">✅ Thank you for your feedback!</p>
        </div>
      )}

      {/* Generated timestamp */}
      <div className="text-xs text-gray-500 border-t pt-2">
        Generated: {new Date(critique.generated_at).toLocaleString()}
      </div>
    </div>
  );
};

export default TradeCritiqueTab;
