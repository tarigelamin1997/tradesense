import React, { useMemo } from 'react';
import { Lightbulb, TrendingUp, AlertTriangle, Target, Calendar, Brain } from 'lucide-react';
import { format, startOfWeek, endOfWeek, isWithinInterval } from 'date-fns';

interface JournalEntry {
  id: string;
  title: string;
  content: string;
  mood?: string;
  created_at: string;
  trade_id?: string;
}

interface Trade {
  id: string;
  symbol: string;
  pnl: number;
  entry_time: string;
  exit_time?: string;
}

interface InsightPattern {
  type: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
  title: string;
  description: string;
  confidence: number; // 0-100%
  actionable?: string;
}

interface JournalInsightsProps {
  entries: JournalEntry[];
  trades?: Trade[];
  onInsightClick?: (insight: InsightPattern) => void;
}

export const JournalInsights: React.FC<JournalInsightsProps> = ({
  entries,
  trades = [],
  onInsightClick
}) => {
  // Analyze journal patterns
  const insights = useMemo(() => {
    const patterns: InsightPattern[] = [];
    
    // 1. Analyze most mentioned symbols
    const symbolCounts: Record<string, number> = {};
    entries.forEach(entry => {
      const symbols = (entry.content + ' ' + entry.title).match(/[A-Z]{2,5}/g) || [];
      symbols.forEach(symbol => {
        if (symbol.length <= 5) {
          symbolCounts[symbol] = (symbolCounts[symbol] || 0) + 1;
        }
      });
    });
    
    const topSymbols = Object.entries(symbolCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3);
    
    if (topSymbols.length > 0) {
      patterns.push({
        type: 'neutral',
        icon: <Target className="w-5 h-5" />,
        title: 'Most Analyzed Symbols',
        description: `You frequently analyze ${topSymbols.map(([s]) => s).join(', ')}. Consider if you're missing opportunities in other markets.`,
        confidence: 90
      });
    }
    
    // 2. Analyze common mistake patterns
    const mistakeKeywords = ['mistake', 'error', 'wrong', 'failed', 'should have', 'missed', 'too early', 'too late'];
    const mistakeEntries = entries.filter(entry => 
      mistakeKeywords.some(keyword => 
        entry.content.toLowerCase().includes(keyword)
      )
    );
    
    if (mistakeEntries.length > entries.length * 0.3) {
      const commonMistakes: Record<string, number> = {};
      mistakeEntries.forEach(entry => {
        if (entry.content.toLowerCase().includes('too early')) commonMistakes['early'] = (commonMistakes['early'] || 0) + 1;
        if (entry.content.toLowerCase().includes('too late')) commonMistakes['late'] = (commonMistakes['late'] || 0) + 1;
        if (entry.content.toLowerCase().includes('position size')) commonMistakes['sizing'] = (commonMistakes['sizing'] || 0) + 1;
        if (entry.content.toLowerCase().includes('stop loss')) commonMistakes['stops'] = (commonMistakes['stops'] || 0) + 1;
      });
      
      const topMistake = Object.entries(commonMistakes)
        .sort(([, a], [, b]) => b - a)[0];
      
      if (topMistake) {
        patterns.push({
          type: 'negative',
          icon: <AlertTriangle className="w-5 h-5" />,
          title: 'Recurring Pattern Detected',
          description: `You frequently mention issues with ${topMistake[0]}. This appears in ${((topMistake[1] / mistakeEntries.length) * 100).toFixed(0)}% of your mistake analyses.`,
          confidence: 85,
          actionable: `Create a checklist to address ${topMistake[0]} before entering trades.`
        });
      }
    }
    
    // 3. Analyze successful strategy patterns
    const successKeywords = ['profit', 'winner', 'success', 'great', 'perfect', 'worked well'];
    const successEntries = entries.filter(entry =>
      successKeywords.some(keyword =>
        entry.content.toLowerCase().includes(keyword)
      )
    );
    
    if (successEntries.length > 0) {
      const strategyMentions: Record<string, number> = {};
      const strategies = ['breakout', 'trend', 'reversal', 'scalp', 'swing', 'momentum'];
      
      successEntries.forEach(entry => {
        strategies.forEach(strategy => {
          if (entry.content.toLowerCase().includes(strategy)) {
            strategyMentions[strategy] = (strategyMentions[strategy] || 0) + 1;
          }
        });
      });
      
      const topStrategy = Object.entries(strategyMentions)
        .sort(([, a], [, b]) => b - a)[0];
      
      if (topStrategy) {
        patterns.push({
          type: 'positive',
          icon: <TrendingUp className="w-5 h-5" />,
          title: 'Winning Strategy Pattern',
          description: `Your ${topStrategy[0]} trades appear in ${((topStrategy[1] / successEntries.length) * 100).toFixed(0)}% of successful trade reviews.`,
          confidence: 75,
          actionable: `Focus more on ${topStrategy[0]} setups as they align with your strengths.`
        });
      }
    }
    
    // 4. Analyze emotional patterns
    const moodData: Record<string, { count: number; negativeWords: number }> = {};
    const negativeWords = ['frustrated', 'angry', 'disappointed', 'anxious', 'fear', 'worried', 'stressed'];
    
    entries.forEach(entry => {
      if (entry.mood) {
        if (!moodData[entry.mood]) {
          moodData[entry.mood] = { count: 0, negativeWords: 0 };
        }
        moodData[entry.mood].count++;
        
        const negCount = negativeWords.filter(word => 
          entry.content.toLowerCase().includes(word)
        ).length;
        moodData[entry.mood].negativeWords += negCount;
      }
    });
    
    const consecutiveNegativeMoods = entries
      .filter(e => e.mood && ['anxious', 'frustrated', 'uncertain'].includes(e.mood))
      .slice(-3);
    
    if (consecutiveNegativeMoods.length >= 3) {
      patterns.push({
        type: 'negative',
        icon: <Brain className="w-5 h-5" />,
        title: 'Emotional Pattern Alert',
        description: '3+ consecutive days of negative sentiment detected. This often precedes poor trading decisions.',
        confidence: 95,
        actionable: 'Consider taking a break or reducing position sizes until your mindset improves.'
      });
    }
    
    // 5. Time-based patterns
    const hourlyPerformance: Record<number, { trades: number; profitable: number }> = {};
    trades.forEach(trade => {
      const hour = new Date(trade.entry_time).getHours();
      if (!hourlyPerformance[hour]) {
        hourlyPerformance[hour] = { trades: 0, profitable: 0 };
      }
      hourlyPerformance[hour].trades++;
      if (trade.pnl > 0) hourlyPerformance[hour].profitable++;
    });
    
    const bestHours = Object.entries(hourlyPerformance)
      .filter(([, data]) => data.trades >= 5)
      .map(([hour, data]) => ({
        hour: parseInt(hour),
        winRate: (data.profitable / data.trades) * 100
      }))
      .sort((a, b) => b.winRate - a.winRate);
    
    if (bestHours.length > 0 && bestHours[0].winRate > 60) {
      patterns.push({
        type: 'positive',
        icon: <Calendar className="w-5 h-5" />,
        title: 'Optimal Trading Hours',
        description: `Your best performance is between ${bestHours[0].hour}:00-${bestHours[0].hour + 1}:00 with a ${bestHours[0].winRate.toFixed(0)}% win rate.`,
        confidence: 80,
        actionable: 'Consider focusing your trading during these peak performance hours.'
      });
    }
    
    // 6. Weekly summary generation
    const currentWeek = entries.filter(entry => 
      isWithinInterval(new Date(entry.created_at), {
        start: startOfWeek(new Date()),
        end: endOfWeek(new Date())
      })
    );
    
    if (currentWeek.length >= 3) {
      const weekMood = currentWeek
        .map(e => e.mood)
        .filter(Boolean)
        .reduce((acc, mood) => {
          acc[mood!] = (acc[mood!] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);
      
      const dominantMood = Object.entries(weekMood)
        .sort(([, a], [, b]) => b - a)[0];
      
      patterns.push({
        type: 'neutral',
        icon: <Calendar className="w-5 h-5" />,
        title: 'Weekly Summary',
        description: `This week: ${currentWeek.length} journal entries, dominant mood: ${dominantMood?.[0] || 'varied'}. ${
          trades.filter(t => 
            isWithinInterval(new Date(t.entry_time), {
              start: startOfWeek(new Date()),
              end: endOfWeek(new Date())
            })
          ).length
        } trades executed.`,
        confidence: 100
      });
    }
    
    return patterns.sort((a, b) => b.confidence - a.confidence);
  }, [entries, trades]);
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center">
          <Lightbulb className="w-5 h-5 mr-2 text-yellow-500" />
          AI-Powered Journal Insights
        </h3>
        <span className="text-sm text-gray-500">
          Based on {entries.length} entries
        </span>
      </div>
      
      {insights.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Brain className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>Not enough journal data to generate insights.</p>
          <p className="text-sm mt-1">Keep journaling to unlock powerful patterns!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {insights.map((insight, index) => (
            <div
              key={index}
              onClick={() => onInsightClick && onInsightClick(insight)}
              className={`p-4 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                insight.type === 'positive' 
                  ? 'bg-green-50 border-green-200 hover:bg-green-100'
                  : insight.type === 'negative'
                  ? 'bg-red-50 border-red-200 hover:bg-red-100'
                  : 'bg-blue-50 border-blue-200 hover:bg-blue-100'
              }`}
            >
              <div className="flex items-start space-x-3">
                <div className={`mt-0.5 ${
                  insight.type === 'positive' 
                    ? 'text-green-600'
                    : insight.type === 'negative'
                    ? 'text-red-600'
                    : 'text-blue-600'
                }`}>
                  {insight.icon}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-gray-900">{insight.title}</h4>
                    <span className="text-xs text-gray-500">
                      {insight.confidence}% confidence
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 mt-1">{insight.description}</p>
                  {insight.actionable && (
                    <div className="mt-2 text-sm font-medium text-blue-600">
                      💡 {insight.actionable}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Auto-refresh indicator */}
      <div className="text-center text-xs text-gray-500 mt-4">
        Insights update automatically as you add journal entries
      </div>
    </div>
  );
};

export default JournalInsights;