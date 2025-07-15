import React, { useState, useMemo } from 'react';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Cell, ScatterChart, Scatter
} from 'recharts';
import { TrendingUp, TrendingDown, Activity, Brain } from 'lucide-react';
import { format } from 'date-fns';

export interface MoodEmoji {
  [key: string]: string;
}

export const moodEmojis: MoodEmoji = {
  confident: '😎',
  anxious: '😰',
  neutral: '😐',
  happy: '😊',
  frustrated: '😤',
  focused: '🎯',
  uncertain: '🤔'
};

interface MoodData {
  date: string;
  mood: string;
  confidence: number;
  pnl?: number;
  winRate?: number;
  tradeCount?: number;
}

interface MoodTrackerProps {
  moodData: MoodData[];
  onMoodSelect?: (mood: string, confidence: number) => void;
  currentMood?: string;
  currentConfidence?: number;
}

export const MoodTracker: React.FC<MoodTrackerProps> = ({
  moodData,
  onMoodSelect,
  currentMood = 'neutral',
  currentConfidence = 5
}) => {
  const [selectedMood, setSelectedMood] = useState(currentMood);
  const [confidence, setConfidence] = useState(currentConfidence);
  const [energyLevel, setEnergyLevel] = useState<'low' | 'medium' | 'high'>('medium');
  const [marketSentiment, setMarketSentiment] = useState<'fearful' | 'neutral' | 'greedy'>('neutral');

  // Calculate mood statistics
  const moodStats = useMemo(() => {
    const stats: Record<string, { count: number; avgPnl: number; avgWinRate: number }> = {};
    
    moodData.forEach(day => {
      if (!stats[day.mood]) {
        stats[day.mood] = { count: 0, avgPnl: 0, avgWinRate: 0 };
      }
      
      stats[day.mood].count++;
      stats[day.mood].avgPnl += day.pnl || 0;
      stats[day.mood].avgWinRate += day.winRate || 0;
    });
    
    // Calculate averages
    Object.keys(stats).forEach(mood => {
      stats[mood].avgPnl = stats[mood].avgPnl / stats[mood].count;
      stats[mood].avgWinRate = stats[mood].avgWinRate / stats[mood].count;
    });
    
    return stats;
  }, [moodData]);

  // Calculate confidence correlation
  const confidenceCorrelation = useMemo(() => {
    const grouped: Record<number, { totalPnl: number; count: number; avgWinRate: number }> = {};
    
    moodData.forEach(day => {
      const conf = day.confidence;
      if (!grouped[conf]) {
        grouped[conf] = { totalPnl: 0, count: 0, avgWinRate: 0 };
      }
      
      grouped[conf].totalPnl += day.pnl || 0;
      grouped[conf].count++;
      grouped[conf].avgWinRate += day.winRate || 0;
    });
    
    return Object.entries(grouped).map(([confidence, data]) => ({
      confidence: parseInt(confidence),
      avgPnl: data.totalPnl / data.count,
      avgWinRate: data.avgWinRate / data.count,
      count: data.count
    })).sort((a, b) => a.confidence - b.confidence);
  }, [moodData]);

  // Get recent mood trends
  const recentTrends = useMemo(() => {
    const recent = moodData.slice(-30); // Last 30 days
    return recent.map(day => ({
      date: format(new Date(day.date), 'MMM d'),
      confidence: day.confidence,
      pnl: day.pnl || 0,
      moodScore: Object.keys(moodEmojis).indexOf(day.mood) - 3 // Convert mood to numeric score
    }));
  }, [moodData]);

  const handleMoodSubmit = () => {
    if (onMoodSelect) {
      onMoodSelect(selectedMood, confidence);
    }
  };

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload[0]) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="text-sm font-medium">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.name.includes('P&L') ? `$${entry.value.toFixed(2)}` : entry.value.toFixed(1)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Current Mood Selector */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4">How are you feeling today?</h3>
        
        <div className="space-y-4">
          {/* Mood Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Mood</label>
            <div className="grid grid-cols-4 gap-2">
              {Object.entries(moodEmojis).map(([mood, emoji]) => (
                <button
                  key={mood}
                  onClick={() => setSelectedMood(mood)}
                  className={`p-3 rounded-lg border-2 transition-all ${
                    selectedMood === mood
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="text-2xl mb-1">{emoji}</div>
                  <div className="text-xs capitalize">{mood}</div>
                </button>
              ))}
            </div>
          </div>
          
          {/* Confidence Level */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confidence Level: <span className="text-blue-600 font-bold">{confidence}/10</span>
            </label>
            <input
              type="range"
              min="1"
              max="10"
              value={confidence}
              onChange={(e) => setConfidence(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${confidence * 10}%, #E5E7EB ${confidence * 10}%, #E5E7EB 100%)`
              }}
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Low</span>
              <span>Medium</span>
              <span>High</span>
            </div>
          </div>
          
          {/* Energy Level */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Energy Level</label>
            <div className="flex space-x-2">
              {(['low', 'medium', 'high'] as const).map(level => (
                <button
                  key={level}
                  onClick={() => setEnergyLevel(level)}
                  className={`flex-1 py-2 px-4 rounded-lg capitalize ${
                    energyLevel === level
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>
          
          {/* Market Sentiment */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Market Sentiment</label>
            <div className="flex space-x-2">
              <button
                onClick={() => setMarketSentiment('fearful')}
                className={`flex-1 py-2 px-4 rounded-lg ${
                  marketSentiment === 'fearful'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                😨 Fearful
              </button>
              <button
                onClick={() => setMarketSentiment('neutral')}
                className={`flex-1 py-2 px-4 rounded-lg ${
                  marketSentiment === 'neutral'
                    ? 'bg-gray-600 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                😐 Neutral
              </button>
              <button
                onClick={() => setMarketSentiment('greedy')}
                className={`flex-1 py-2 px-4 rounded-lg ${
                  marketSentiment === 'greedy'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                🤑 Greedy
              </button>
            </div>
          </div>
          
          <button
            onClick={handleMoodSubmit}
            className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Save Mood Data
          </button>
        </div>
      </div>
      
      {/* Mood Performance Analysis */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <Brain className="w-5 h-5 mr-2" />
          Mood Performance Analysis
        </h3>
        
        {/* Mood vs P&L Bar Chart */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Average P&L by Mood</h4>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={Object.entries(moodStats).map(([mood, stats]) => ({
              mood: moodEmojis[mood] + ' ' + mood,
              avgPnl: stats.avgPnl,
              count: stats.count
            }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="mood" />
              <YAxis />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="avgPnl" name="Avg P&L">
                {Object.entries(moodStats).map(([mood, stats], index) => (
                  <Cell key={`cell-${index}`} fill={stats.avgPnl >= 0 ? '#10B981' : '#EF4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        {/* Confidence vs Performance Scatter */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Confidence Level vs Performance</h4>
          <ResponsiveContainer width="100%" height={200}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="confidence" 
                domain={[1, 10]} 
                ticks={[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
                label={{ value: 'Confidence Level', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                dataKey="avgPnl"
                label={{ value: 'Avg P&L ($)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Scatter 
                name="Avg P&L" 
                data={confidenceCorrelation} 
                fill="#3B82F6"
              />
            </ScatterChart>
          </ResponsiveContainer>
          <p className="text-xs text-gray-500 text-center mt-2">
            {confidenceCorrelation.length > 0 && 
              `Best performance at confidence level ${
                confidenceCorrelation.reduce((best, curr) => 
                  curr.avgPnl > best.avgPnl ? curr : best
                ).confidence
              }`
            }
          </p>
        </div>
        
        {/* Recent Mood Trends */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">30-Day Mood & Performance Trend</h4>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={recentTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip content={<CustomTooltip />} />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="confidence" 
                stroke="#3B82F6" 
                name="Confidence"
                strokeWidth={2}
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="pnl" 
                stroke="#10B981" 
                name="P&L"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      {/* Insights */}
      <div className="bg-blue-50 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-900 mb-2 flex items-center">
          <Activity className="w-4 h-4 mr-2" />
          Emotional Intelligence Insights
        </h4>
        <ul className="space-y-1 text-sm text-blue-800">
          {Object.entries(moodStats).length > 0 && (
            <>
              <li>• Your best mood for trading: {
                Object.entries(moodStats).reduce((best, [mood, stats]) => 
                  stats.avgPnl > moodStats[best].avgPnl ? mood : best
                , Object.keys(moodStats)[0])
              }</li>
              <li>• Optimal confidence range: {
                confidenceCorrelation.length > 0 
                  ? `${Math.max(1, confidenceCorrelation.reduce((best, curr) => 
                      curr.avgPnl > best.avgPnl ? curr : best
                    ).confidence - 1)}-${Math.min(10, confidenceCorrelation.reduce((best, curr) => 
                      curr.avgPnl > best.avgPnl ? curr : best
                    ).confidence + 1)}`
                  : 'Not enough data'
              }</li>
              <li>• Consider smaller positions when feeling anxious or frustrated</li>
            </>
          )}
        </ul>
      </div>
    </div>
  );
};

export default MoodTracker;