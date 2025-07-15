interface SentimentResult {
  score: number;
  comparative: number;
  sentiment: 'positive' | 'negative' | 'neutral';
  tokens: string[];
  positive: string[];
  negative: string[];
}

// Trading-specific sentiment words
const tradingLexicon = {
  positive: {
    // General positive
    'profit': 3,
    'winner': 3,
    'success': 2,
    'gain': 2,
    'green': 2,
    'up': 1,
    'bullish': 2,
    'perfect': 3,
    'excellent': 3,
    'great': 2,
    'good': 1,
    'confident': 2,
    'strong': 2,
    'solid': 2,
    'breakout': 1,
    'momentum': 1,
    'trend': 1,
    
    // Execution
    'executed': 1,
    'managed': 1,
    'disciplined': 2,
    'patient': 2,
    'focused': 2,
    'controlled': 2,
    
    // Analysis
    'correct': 2,
    'accurate': 2,
    'confirmed': 1,
    'validated': 1,
    'worked': 2
  },
  
  negative: {
    // General negative
    'loss': -3,
    'loser': -3,
    'mistake': -2,
    'error': -2,
    'wrong': -2,
    'red': -2,
    'down': -1,
    'bearish': -2,
    'terrible': -3,
    'horrible': -3,
    'bad': -1,
    'poor': -2,
    'weak': -2,
    'failed': -3,
    
    // Emotions
    'frustrated': -2,
    'angry': -3,
    'anxious': -2,
    'worried': -2,
    'scared': -2,
    'fear': -3,
    'panic': -3,
    'stressed': -2,
    'disappointed': -2,
    
    // Execution issues
    'missed': -2,
    'late': -1,
    'early': -1,
    'chased': -2,
    'revenge': -3,
    'overtrade': -3,
    'impulsive': -3,
    'fomo': -3,
    'greed': -2
  }
};

// Negation words that reverse sentiment
const negationWords = ['not', 'no', "n't", 'never', 'neither', 'nor', 'none'];

// Intensifier words that amplify sentiment
const intensifiers = {
  'very': 1.5,
  'extremely': 2,
  'really': 1.5,
  'absolutely': 2,
  'totally': 1.5,
  'completely': 2,
  'utterly': 2,
  'quite': 1.25,
  'somewhat': 0.75,
  'slightly': 0.5,
  'barely': 0.5
};

export function analyzeSentiment(text: string): SentimentResult {
  // Normalize and tokenize
  const normalizedText = text.toLowerCase();
  const tokens = normalizedText
    .replace(/[^\w\s'-]/g, ' ')
    .split(/\s+/)
    .filter(token => token.length > 0);
  
  let score = 0;
  const positive: string[] = [];
  const negative: string[] = [];
  
  // Analyze each token with context
  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];
    let tokenScore = 0;
    
    // Check positive words
    if (tradingLexicon.positive[token as keyof typeof tradingLexicon.positive]) {
      tokenScore = tradingLexicon.positive[token as keyof typeof tradingLexicon.positive];
      positive.push(token);
    }
    
    // Check negative words
    if (tradingLexicon.negative[token as keyof typeof tradingLexicon.negative]) {
      tokenScore = tradingLexicon.negative[token as keyof typeof tradingLexicon.negative];
      negative.push(token);
    }
    
    // Check for negation in previous 2 words
    let negated = false;
    for (let j = Math.max(0, i - 2); j < i; j++) {
      if (negationWords.includes(tokens[j])) {
        negated = true;
        break;
      }
    }
    
    if (negated) {
      tokenScore = -tokenScore; // Reverse the sentiment
    }
    
    // Check for intensifiers in previous word
    if (i > 0 && intensifiers[tokens[i - 1] as keyof typeof intensifiers]) {
      tokenScore *= intensifiers[tokens[i - 1] as keyof typeof intensifiers];
    }
    
    score += tokenScore;
  }
  
  // Calculate comparative score (normalized by token count)
  const comparative = tokens.length > 0 ? score / tokens.length : 0;
  
  // Determine overall sentiment
  let sentiment: 'positive' | 'negative' | 'neutral';
  if (score > 1) {
    sentiment = 'positive';
  } else if (score < -1) {
    sentiment = 'negative';
  } else {
    sentiment = 'neutral';
  }
  
  return {
    score,
    comparative,
    sentiment,
    tokens,
    positive,
    negative
  };
}

// Analyze sentiment trends over time
export function analyzeSentimentTrends(entries: Array<{ content: string; date: string }>) {
  return entries.map(entry => ({
    date: entry.date,
    ...analyzeSentiment(entry.content)
  }));
}

// Get sentiment statistics
export function getSentimentStats(entries: Array<{ content: string }>) {
  const sentiments = entries.map(entry => analyzeSentiment(entry.content));
  
  const stats = {
    totalEntries: entries.length,
    positive: sentiments.filter(s => s.sentiment === 'positive').length,
    negative: sentiments.filter(s => s.sentiment === 'negative').length,
    neutral: sentiments.filter(s => s.sentiment === 'neutral').length,
    averageScore: sentiments.reduce((sum, s) => sum + s.score, 0) / sentiments.length,
    mostPositiveWords: [] as Array<{ word: string; count: number }>,
    mostNegativeWords: [] as Array<{ word: string; count: number }>
  };
  
  // Count word frequencies
  const positiveWordCounts: Record<string, number> = {};
  const negativeWordCounts: Record<string, number> = {};
  
  sentiments.forEach(sentiment => {
    sentiment.positive.forEach(word => {
      positiveWordCounts[word] = (positiveWordCounts[word] || 0) + 1;
    });
    sentiment.negative.forEach(word => {
      negativeWordCounts[word] = (negativeWordCounts[word] || 0) + 1;
    });
  });
  
  // Get top words
  stats.mostPositiveWords = Object.entries(positiveWordCounts)
    .map(([word, count]) => ({ word, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);
  
  stats.mostNegativeWords = Object.entries(negativeWordCounts)
    .map(([word, count]) => ({ word, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);
  
  return stats;
}

// Detect emotional patterns that might affect trading
export function detectEmotionalPatterns(entries: Array<{ content: string; date: string }>) {
  const patterns = [];
  
  // Sort entries by date
  const sortedEntries = [...entries].sort((a, b) => 
    new Date(a.date).getTime() - new Date(b.date).getTime()
  );
  
  // Check for consecutive negative days
  let consecutiveNegative = 0;
  let negativeStreak = [];
  
  for (const entry of sortedEntries) {
    const sentiment = analyzeSentiment(entry.content);
    
    if (sentiment.sentiment === 'negative') {
      consecutiveNegative++;
      negativeStreak.push(entry.date);
    } else {
      if (consecutiveNegative >= 3) {
        patterns.push({
          type: 'negative_streak',
          description: `${consecutiveNegative} consecutive days of negative sentiment`,
          dates: [...negativeStreak],
          severity: Math.min(consecutiveNegative / 3, 3) // 1-3 scale
        });
      }
      consecutiveNegative = 0;
      negativeStreak = [];
    }
  }
  
  // Check for revenge trading patterns
  const revengeTradingKeywords = ['revenge', 'make back', 'recover losses', 'get even', 'win back'];
  const revengeEntries = entries.filter(entry =>
    revengeTradingKeywords.some(keyword =>
      entry.content.toLowerCase().includes(keyword)
    )
  );
  
  if (revengeEntries.length > 0) {
    patterns.push({
      type: 'revenge_trading',
      description: 'Potential revenge trading mindset detected',
      dates: revengeEntries.map(e => e.date),
      severity: Math.min(revengeEntries.length / entries.length * 10, 3)
    });
  }
  
  // Check for overconfidence patterns
  const overconfidenceKeywords = ['easy money', 'cant lose', "can't lose", 'guaranteed', 'sure thing', 'killing it'];
  const overconfidentEntries = entries.filter(entry =>
    overconfidenceKeywords.some(keyword =>
      entry.content.toLowerCase().includes(keyword)
    )
  );
  
  if (overconfidentEntries.length > 0) {
    patterns.push({
      type: 'overconfidence',
      description: 'Signs of overconfidence detected',
      dates: overconfidentEntries.map(e => e.date),
      severity: Math.min(overconfidentEntries.length / entries.length * 10, 3)
    });
  }
  
  return patterns;
}