interface SentimentResult {
	score: number; // -1 to 1
	magnitude: number; // 0 to 1
	sentiment: 'positive' | 'negative' | 'neutral';
	keywords: string[];
	emotions: {
		joy: number;
		fear: number;
		anger: number;
		sadness: number;
		confidence: number;
		anxiety: number;
	};
}

// Simple sentiment analysis based on keyword matching
// In production, this would use a proper NLP API
export function analyzeSentiment(text: string): SentimentResult {
	const lowerText = text.toLowerCase();
	
	// Sentiment keywords
	const positiveWords = [
		'good', 'great', 'excellent', 'profit', 'win', 'winning', 'successful',
		'confident', 'happy', 'excited', 'optimistic', 'strong', 'perfect',
		'amazing', 'fantastic', 'wonderful', 'achieved', 'goal', 'gains',
		'disciplined', 'patient', 'focused', 'calm', 'clear', 'momentum'
	];
	
	const negativeWords = [
		'bad', 'loss', 'lost', 'mistake', 'wrong', 'failed', 'failure',
		'frustrated', 'angry', 'disappointed', 'fear', 'scared', 'worried',
		'anxious', 'stress', 'terrible', 'awful', 'horrible', 'missed',
		'regret', 'stupid', 'foolish', 'impulsive', 'undisciplined'
	];
	
	// Emotion keywords
	const emotionKeywords = {
		joy: ['happy', 'excited', 'thrilled', 'elated', 'joyful', 'celebrating'],
		fear: ['afraid', 'scared', 'fearful', 'terrified', 'worried', 'nervous'],
		anger: ['angry', 'furious', 'mad', 'irritated', 'annoyed', 'frustrated'],
		sadness: ['sad', 'depressed', 'down', 'unhappy', 'disappointed', 'miserable'],
		confidence: ['confident', 'sure', 'certain', 'decisive', 'bold', 'assured'],
		anxiety: ['anxious', 'nervous', 'worried', 'tense', 'stressed', 'uneasy']
	};
	
	// Count sentiment words
	let positiveCount = 0;
	let negativeCount = 0;
	const foundKeywords = new Set<string>();
	
	positiveWords.forEach(word => {
		if (lowerText.includes(word)) {
			positiveCount++;
			foundKeywords.add(word);
		}
	});
	
	negativeWords.forEach(word => {
		if (lowerText.includes(word)) {
			negativeCount++;
			foundKeywords.add(word);
		}
	});
	
	// Calculate sentiment score
	const totalWords = text.split(/\s+/).length;
	const sentimentWords = positiveCount + negativeCount;
	const score = sentimentWords > 0 
		? (positiveCount - negativeCount) / sentimentWords 
		: 0;
	
	// Calculate magnitude (intensity)
	const magnitude = Math.min(sentimentWords / totalWords * 10, 1);
	
	// Determine overall sentiment
	let sentiment: 'positive' | 'negative' | 'neutral';
	if (score > 0.2) sentiment = 'positive';
	else if (score < -0.2) sentiment = 'negative';
	else sentiment = 'neutral';
	
	// Calculate emotion scores
	const emotions = {
		joy: 0,
		fear: 0,
		anger: 0,
		sadness: 0,
		confidence: 0,
		anxiety: 0
	};
	
	Object.entries(emotionKeywords).forEach(([emotion, keywords]) => {
		let count = 0;
		keywords.forEach(keyword => {
			if (lowerText.includes(keyword)) {
				count++;
			}
		});
		emotions[emotion as keyof typeof emotions] = Math.min(count / keywords.length, 1);
	});
	
	return {
		score,
		magnitude,
		sentiment,
		keywords: Array.from(foundKeywords),
		emotions
	};
}

// Analyze trading performance from journal text
export function analyzeTradingMindset(entries: Array<{ content: string; date: string }>): {
	overallSentiment: 'positive' | 'negative' | 'neutral';
	sentimentTrend: 'improving' | 'declining' | 'stable';
	dominantEmotions: string[];
	suggestions: string[];
} {
	if (entries.length === 0) {
		return {
			overallSentiment: 'neutral',
			sentimentTrend: 'stable',
			dominantEmotions: [],
			suggestions: ['Start journaling to track your trading mindset']
		};
	}
	
	// Analyze all entries
	const analyses = entries.map(entry => analyzeSentiment(entry.content));
	
	// Calculate overall sentiment
	const avgScore = analyses.reduce((sum, a) => sum + a.score, 0) / analyses.length;
	let overallSentiment: 'positive' | 'negative' | 'neutral';
	if (avgScore > 0.2) overallSentiment = 'positive';
	else if (avgScore < -0.2) overallSentiment = 'negative';
	else overallSentiment = 'neutral';
	
	// Calculate sentiment trend (compare recent vs older)
	let sentimentTrend: 'improving' | 'declining' | 'stable' = 'stable';
	if (analyses.length >= 3) {
		const recentAvg = analyses.slice(-3).reduce((sum, a) => sum + a.score, 0) / 3;
		const olderAvg = analyses.slice(0, -3).reduce((sum, a) => sum + a.score, 0) / Math.max(analyses.length - 3, 1);
		
		if (recentAvg > olderAvg + 0.1) sentimentTrend = 'improving';
		else if (recentAvg < olderAvg - 0.1) sentimentTrend = 'declining';
	}
	
	// Find dominant emotions
	const emotionTotals = {
		joy: 0,
		fear: 0,
		anger: 0,
		sadness: 0,
		confidence: 0,
		anxiety: 0
	};
	
	analyses.forEach(analysis => {
		Object.entries(analysis.emotions).forEach(([emotion, score]) => {
			emotionTotals[emotion as keyof typeof emotionTotals] += score;
		});
	});
	
	const dominantEmotions = Object.entries(emotionTotals)
		.sort(([, a], [, b]) => b - a)
		.slice(0, 3)
		.filter(([, score]) => score > 0.5)
		.map(([emotion]) => emotion);
	
	// Generate suggestions based on analysis
	const suggestions: string[] = [];
	
	if (overallSentiment === 'negative') {
		suggestions.push('Consider taking a break to reset your mindset');
		suggestions.push('Review your risk management rules');
	}
	
	if (emotionTotals.fear > emotionTotals.confidence) {
		suggestions.push('Work on building confidence through smaller position sizes');
	}
	
	if (emotionTotals.anger > 1) {
		suggestions.push('Implement a cooling-off period after losses');
	}
	
	if (sentimentTrend === 'declining') {
		suggestions.push('Your mood is trending negative - consider reducing trading frequency');
	}
	
	if (dominantEmotions.includes('anxiety')) {
		suggestions.push('Practice relaxation techniques before trading sessions');
	}
	
	if (overallSentiment === 'positive' && dominantEmotions.includes('confidence')) {
		suggestions.push('Your positive mindset is great - stay disciplined and stick to your plan');
	}
	
	return {
		overallSentiment,
		sentimentTrend,
		dominantEmotions,
		suggestions
	};
}