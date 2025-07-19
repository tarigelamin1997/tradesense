import { api } from './client';

export interface AnalyticsSummary {
	total_pnl: number;
	total_pnl_percentage: number;
	win_rate: number;
	win_rate_change: number;
	total_trades: number;
	avg_hold_time: string;
	current_streak: {
		type: 'win' | 'loss';
		count: number;
	};
	profit_factor: number;
	sharpe_ratio: number;
}

export interface EquityPoint {
	date: string;
	value: number;
	trades?: number;
}

export interface DailyPnL {
	date: string;
	pnl: number;
	trades: number;
}

export interface AnalyticsData {
	summary: AnalyticsSummary;
	equity_curve: EquityPoint[];
	daily_pnl: DailyPnL[];
	monthly_pnl: Array<{
		month: string;
		pnl: number;
		trades: number;
	}>;
	strategy_breakdown: Array<{
		name: string;
		value: number;
		pnl: number;
	}>;
	win_distribution: {
		wins: number;
		losses: number;
		breakeven: number;
	};
}

export interface DateRange {
	start_date?: string;
	end_date?: string;
	period?: '7d' | '30d' | '90d' | '1y' | 'all';
}

export const analyticsApi = {
	// Get comprehensive analytics
	async getAnalytics(range?: DateRange): Promise<AnalyticsData> {
		// For now, just get the summary and construct the full data
		const summary = await this.getSummary(range);
		
		// Return mock data structure with real summary
		return {
			summary,
			equity_curve: [],
			daily_pnl: [],
			monthly_pnl: [],
			strategy_breakdown: [],
			win_distribution: {
				wins: 0,
				losses: 0,
				breakeven: 0
			}
		};
	},

	// Get summary statistics
	async getSummary(range?: DateRange): Promise<AnalyticsSummary> {
		return api.get('/api/v1/analytics/summary', range);
	},

	// Get equity curve data
	async getEquityCurve(range?: DateRange): Promise<EquityPoint[]> {
		return api.get('/api/v1/analytics/equity-curve', range);
	},

	// Get daily P&L
	async getDailyPnL(range?: DateRange): Promise<DailyPnL[]> {
		return api.get('/api/v1/analytics/daily-pnl', range);
	},

	// Get performance by strategy
	async getStrategyPerformance(): Promise<Array<{
		strategy: string;
		trades: number;
		pnl: number;
		win_rate: number;
	}>> {
		return api.get('/api/v1/analytics/strategies');
	},

	// Get performance by symbol
	async getSymbolPerformance(): Promise<Array<{
		symbol: string;
		trades: number;
		pnl: number;
		win_rate: number;
	}>> {
		return api.get('/api/v1/analytics/symbols');
	},

	// Get calendar heatmap data
	async getCalendarData(year: number): Promise<Array<{
		date: string;
		pnl: number;
		trades: number;
	}>> {
		return api.get(`/api/v1/analytics/calendar/${year}`);
	}
};