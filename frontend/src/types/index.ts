
export interface User {
  id: string;
  username: string;
  email: string;
  role: 'user' | 'admin' | 'partner';
  partnerId?: string;
}

export interface Trade {
  id: string;
  symbol: string;
  entryTime: string;
  exitTime: string;
  entryPrice: number;
  exitPrice: number;
  qty: number;
  direction: 'long' | 'short';
  pnl: number;
  tradeType: 'futures' | 'stocks' | 'options' | 'forex' | 'crypto';
  broker: string;
  notes?: string;
  commission?: number;
  stopLoss?: number;
  takeProfit?: number;
}

export interface DashboardMetrics {
  totalTrades: number;
  winRate: number;
  profitFactor: number;
  totalPnl: number;
  bestDay: number;
  worstDay: number;
  avgWin: number;
  avgLoss: number;
  maxDrawdown: number;
  sharpeRatio: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  success: boolean;
  token?: string;
  user?: User;
  message?: string;
}
