import { api } from './client';

export interface Trade {
	id: number;
	user_id: string;
	symbol: string;
	side: 'long' | 'short';
	entry_price: number;
	exit_price: number;
	quantity: number;
	entry_date: string;
	exit_date: string;
	pnl?: number;
	pnl_percentage?: number;
	strategy?: string;
	notes?: string;
	created_at?: string;
	updated_at?: string;
}

export interface TradeFilters {
	symbol?: string;
	side?: 'long' | 'short';
	date_from?: string;
	date_to?: string;
	strategy?: string;
	min_pnl?: number;
	max_pnl?: number;
	limit?: number;
	offset?: number;
}

export interface TradeStats {
	total_trades: number;
	total_pnl: number;
	win_rate: number;
	avg_win: number;
	avg_loss: number;
	profit_factor: number;
	best_trade: number;
	worst_trade: number;
	avg_duration_minutes: number;
}

export const tradesApi = {
	// Get all trades with optional filters
	async getTrades(filters?: TradeFilters): Promise<Trade[]> {
		return api.get('/api/v1/trades/', filters);
	},

	// Get a single trade
	async getTrade(id: number): Promise<Trade> {
		return api.get(`/api/v1/trades/${id}`);
	},

	// Create a new trade
	async createTrade(trade: Omit<Trade, 'id' | 'created_at' | 'updated_at'>): Promise<Trade> {
		return api.post('/api/v1/trades/', trade);
	},

	// Update a trade
	async updateTrade(id: number, trade: Partial<Trade>): Promise<Trade> {
		return api.put(`/api/v1/trades/${id}`, trade);
	},

	// Delete a trade
	async deleteTrade(id: number): Promise<void> {
		return api.delete(`/api/v1/trades/${id}`);
	},

	// Get trade statistics
	async getStats(filters?: TradeFilters): Promise<TradeStats> {
		return api.get('/api/v1/trades/stats/', filters);
	},

	// Bulk operations
	async bulkDelete(ids: number[]): Promise<void> {
		return api.post('/api/v1/trades/bulk-delete/', { ids });
	},

	// Export trades
	async exportTrades(format: 'csv' | 'json' = 'csv'): Promise<Blob> {
		const response = await api.get(`/api/v1/trades/export/?format=${format}`, {
			responseType: 'blob'
		});
		return response;
	}
};