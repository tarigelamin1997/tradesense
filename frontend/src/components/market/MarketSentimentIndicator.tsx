
import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';

interface MarketSentiment {
  symbol: string;
  sentiment_score: number;
  sentiment_label: string;
  fear_greed_index: number;
  volatility_percentile: number;
  news_sentiment: string;
  social_sentiment: string;
}

interface MarketSentimentIndicatorProps {
  symbol: string;
}

export const MarketSentimentIndicator: React.FC<MarketSentimentIndicatorProps> = ({ symbol }) => {
  const [sentiment, setSentiment] = useState<MarketSentiment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSentiment = async () => {
      try {
        const response = await fetch(`/api/v1/market-data/sentiment/${symbol}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (!response.ok) throw new Error('Failed to fetch sentiment');
        
        const data = await response.json();
        setSentiment(data.data);
      } catch (err) {
        console.error('Error fetching sentiment:', err);
      } finally {
        setLoading(false);
      }
    };

    if (symbol) {
      fetchSentiment();
    }
  }, [symbol]);

  const getSentimentColor = (label: string): string => {
    switch (label) {
      case 'bullish': return 'text-green-600 bg-green-100';
      case 'bearish': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getFearGreedColor = (index: number): string => {
    if (index <= 25) return 'text-red-600';
    if (index <= 45) return 'text-orange-600';
    if (index <= 55) return 'text-yellow-600';
    if (index <= 75) return 'text-green-600';
    return 'text-blue-600';
  };

  if (loading || !sentiment) {
    return (
      <Card className="p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-2">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-12 bg-gray-200 rounded"></div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-4">
      <h3 className="text-lg font-semibold mb-4">Market Sentiment - {symbol}</h3>
      
      <div className="space-y-4">
        {/* Overall Sentiment */}
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Overall Sentiment</span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSentimentColor(sentiment.sentiment_label)}`}>
            {sentiment.sentiment_label.toUpperCase()}
          </span>
        </div>

        {/* Sentiment Score Bar */}
        <div>
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Bearish</span>
            <span>Neutral</span>
            <span>Bullish</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(sentiment.sentiment_score + 1) * 50}%` }}
            ></div>
          </div>
          <div className="text-center text-sm text-gray-600 mt-1">
            Score: {sentiment.sentiment_score.toFixed(2)}
          </div>
        </div>

        {/* Fear & Greed Index */}
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Fear & Greed Index</span>
          <span className={`font-bold ${getFearGreedColor(sentiment.fear_greed_index)}`}>
            {sentiment.fear_greed_index}
          </span>
        </div>

        {/* Volatility */}
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Volatility Percentile</span>
          <span className="font-medium">
            {sentiment.volatility_percentile}%
          </span>
        </div>

        {/* News & Social Sentiment */}
        <div className="grid grid-cols-2 gap-4 pt-2 border-t">
          <div className="text-center">
            <div className="text-sm text-gray-600">News</div>
            <div className={`text-sm font-medium px-2 py-1 rounded ${getSentimentColor(sentiment.news_sentiment)}`}>
              {sentiment.news_sentiment}
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-600">Social</div>
            <div className={`text-sm font-medium px-2 py-1 rounded ${getSentimentColor(sentiment.social_sentiment)}`}>
              {sentiment.social_sentiment}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
