import { writable } from 'svelte/store';

export interface Trade {
	id: number;
	symbol: string;
	side: 'long' | 'short';
	entryPrice: number;
	exitPrice: number;
	quantity: number;
	pnl: number;
	entryDate: string;
	exitDate: string;
}

function createTradeStore() {
	const { subscribe, set, update } = writable<Trade[]>([]);

	return {
		subscribe,
		setTrades: (trades: Trade[]) => set(trades),
		addTrade: (trade: Trade) => update(trades => [...trades, trade]),
		updateTrade: (id: number, updates: Partial<Trade>) => update(trades => 
			trades.map(t => t.id === id ? { ...t, ...updates } : t)
		),
		deleteTrade: (id: number) => update(trades => trades.filter(t => t.id !== id)),
		reset: () => set([])
	};
}

export const tradeStore = createTradeStore();