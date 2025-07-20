import { api } from './client-safe';

export interface PerformanceSummary {
	total_trades: number;
	total_pnl: number;
	win_rate: number;
	profit_factor: number;
	sharpe_ratio: number;
	max_drawdown: number;
	avg_win: number;
	avg_loss: number;
	best_trade: number;
	worst_trade: number;
	avg_trade_duration: string;
}

export interface StreakAnalysis {
	current_streak: number;
	current_streak_type: 'win' | 'loss' | 'neutral';
	max_win_streak: number;
	max_loss_streak: number;
	avg_win_streak: number;
	avg_loss_streak: number;
	streak_history: Array<{
		type: 'win' | 'loss';
		count: number;
		pnl: number;
		start_date: string;
		end_date: string;
	}>;
}

export interface HeatmapData {
	daily_pnl: Record<string, number>;
	hourly_performance: Record<number, { count: number; pnl: number; win_rate: number }>;
	weekday_performance: Record<string, { count: number; pnl: number; win_rate: number }>;
	monthly_performance: Record<string, { count: number; pnl: number; win_rate: number }>;
}

export interface EmotionalAnalytics {
	emotion_performance: Record<string, {
		count: number;
		pnl: number;
		win_rate: number;
		avg_pnl: number;
	}>;
	confidence_correlation: {
		correlation: number;
		confidence_levels: Array<{
			level: number;
			avg_pnl: number;
			win_rate: number;
			count: number;
		}>;
	};
	mood_trends: Array<{
		date: string;
		mood_score: number;
		pnl: number;
	}>;
}

export interface MarketRegime {
	current_regime: 'trending' | 'ranging' | 'volatile';
	regime_performance: Record<string, {
		count: number;
		pnl: number;
		win_rate: number;
		avg_pnl: number;
	}>;
	recommendations: string[];
}

export interface TradeIntelligence {
	patterns: Array<{
		pattern_name: string;
		frequency: number;
		win_rate: number;
		avg_pnl: number;
		description: string;
	}>;
	optimal_conditions: {
		best_time: string;
		best_day: string;
		best_strategy: string;
		best_symbols: string[];
	};
	risk_analysis: {
		var_95: number;
		expected_shortfall: number;
		risk_adjusted_return: number;
		recommendations: string[];
	};
}

export interface TradeCritique {
	trade_id: number;
	score: number;
	strengths: string[];
	weaknesses: string[];
	recommendations: string[];
	similar_trades: Array<{
		trade_id: number;
		similarity_score: number;
		outcome: 'better' | 'worse';
	}>;
}

export const analyticsAdvancedApi = {
	// Performance Analytics
	async getPerformanceSummary(): Promise<PerformanceSummary> {
		return api.get('/api/v1/analytics/performance/summary');
	},

	async getPerformanceVitals(): Promise<any> {
		return api.get('/api/v1/analytics/performance/vitals');
	},

	// Streak Analysis
	async getStreakAnalysis(): Promise<StreakAnalysis> {
		return api.get('/api/v1/analytics/streaks/streaks');
	},

	async getStreakSummary(): Promise<any> {
		return api.get('/api/v1/analytics/streaks/streaks/summary');
	},

	// Heatmap Analytics
	async getHeatmapData(): Promise<HeatmapData> {
		return api.get('/api/v1/analytics/heatmap/heatmap');
	},

	async getSymbolHeatmap(): Promise<any> {
		return api.get('/api/v1/analytics/heatmap/heatmap/symbols');
	},

	async getTimeHeatmap(): Promise<any> {
		return api.get('/api/v1/analytics/heatmap/heatmap/time');
	},

	// Strategy Performance
	async getStrategyPerformance(): Promise<any> {
		return api.get('/api/v1/analytics/strategy-performance');
	},

	// Emotional Analytics
	async getEmotionImpact(): Promise<EmotionalAnalytics> {
		return api.get('/api/v1/analytics/emotion-impact');
	},

	async getConfidenceCorrelation(): Promise<any> {
		return api.get('/api/v1/analytics/confidence-correlation');
	},

	async getEmotionalInsights(): Promise<any> {
		return api.get('/api/v1/emotions/insights');
	},

	async getEmotionalTrends(): Promise<any> {
		return api.get('/api/v1/emotions/analytics/trends');
	},

	// Market Intelligence
	async getMarketRegime(): Promise<MarketRegime> {
		return api.get('/api/v1/intelligence/market-regime');
	},

	async analyzePatterns(): Promise<TradeIntelligence> {
		return api.get('/api/v1/intelligence/analyze-patterns');
	},

	async getMarketAlerts(): Promise<any> {
		return api.get('/api/v1/intelligence/market-alerts');
	},

	async getPerformanceForecast(): Promise<any> {
		return api.get('/api/v1/intelligence/performance-forecast');
	},

	// Trade Critique
	async getTradeCritique(tradeId: number): Promise<TradeCritique> {
		return api.get(`/api/v1/critique/trades/${tradeId}`);
	},

	async getCritiqueAnalytics(): Promise<any> {
		return api.get('/api/v1/critique/analytics');
	},

	// Playbook Analytics
	async getAvailablePlaybooks(): Promise<any> {
		return api.get('/api/v1/analytics/playbooks/available');
	},

	async comparePlaybooks(playbooks: string[]): Promise<any> {
		return api.post('/api/v1/analytics/playbooks/compare', { playbooks });
	},

	async optimizePlaybook(playbookName: string): Promise<any> {
		return api.get(`/api/v1/analytics/playbooks/${playbookName}/optimization`);
	},

	// Timeline Analysis
	async getTimeline(): Promise<any> {
		return api.get('/api/v1/analytics/timeline');
	}
};