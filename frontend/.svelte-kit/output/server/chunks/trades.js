import { w as writable } from "./index.js";
function createTradeStore() {
  const { subscribe, set, update } = writable([]);
  return {
    subscribe,
    setTrades: (trades) => set(trades),
    addTrade: (trade) => update((trades) => [...trades, trade]),
    updateTrade: (id, updates) => update(
      (trades) => trades.map((t) => t.id === id ? { ...t, ...updates } : t)
    ),
    deleteTrade: (id) => update((trades) => trades.filter((t) => t.id !== id)),
    reset: () => set([])
  };
}
createTradeStore();
