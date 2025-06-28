import { api } from './api';

export interface MarketQuote {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  timestamp: number;
}

export interface MarketRegime {
  regime: 'bull_trending' | 'bear_trending' | 'sideways_choppy' | 'high_volatility' | 'low_volatility';
  confidence: number;
  duration_days: number;
  key_indicators: Record<string, number>;
  recommended_strategies: string[];
  risk_level: 'Low' | 'Medium' | 'High';
}

class MarketDataService {
  private ws: WebSocket | null = null;
  private subscribers: Map<string, Set<(data: MarketQuote) => void>> = new Map();

  // Real-time WebSocket connection
  connectToRealTimeData() {
    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/api/v1/market-data/ws/market-data`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('Connected to real-time market data');
    };

    this.ws.onmessage = (event) => {
      const data: MarketQuote = JSON.parse(event.data);
      this.notifySubscribers(data.symbol, data);
    };

    this.ws.onclose = () => {
      console.log('Disconnected from market data');
      // Attempt to reconnect after 5 seconds
      setTimeout(() => this.connectToRealTimeData(), 5000);
    };
  }

  // Subscribe to real-time updates for a symbol
  subscribeToSymbol(symbol: string, callback: (data: MarketQuote) => void) {
    if (!this.subscribers.has(symbol)) {
      this.subscribers.set(symbol, new Set());
    }

    this.subscribers.get(symbol)!.add(callback);

    // Send subscription message
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        symbol: symbol
      }));
    }
  }

  // Unsubscribe from symbol updates
  unsubscribeFromSymbol(symbol: string, callback: (data: MarketQuote) => void) {
    const symbolSubscribers = this.subscribers.get(symbol);
    if (symbolSubscribers) {
      symbolSubscribers.delete(callback);
      if (symbolSubscribers.size === 0) {
        this.subscribers.delete(symbol);
      }
    }
  }

  private notifySubscribers(symbol: string, data: MarketQuote) {
    const symbolSubscribers = this.subscribers.get(symbol);
    if (symbolSubscribers) {
      symbolSubscribers.forEach(callback => callback(data));
    }
  }

  // Get current market regime analysis
  async getMarketRegime(): Promise<MarketRegime> {
    const response = await api.get('/market-data/regime-analysis');
    return response.data;
  }

  // Get live quote for a symbol
  async getLiveQuote(symbol: string): Promise<MarketQuote> {
    const response = await api.get(`/market-data/symbols/${symbol}/live`);
    return response.data;
  }

  // Get market hours and status
  async getMarketHours() {
    const response = await api.get('/market-data/market-hours');
    return response.data;
  }

  // Get trending symbols
  async getTrendingSymbols() {
    const response = await api.get('/market-data/trending');
    return response.data;
  }

  // Disconnect WebSocket
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const marketDataService = new MarketDataService();