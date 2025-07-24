// Core type definitions for TradeSense

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'user' | 'admin' | 'trader';
  subscription: SubscriptionTier;
  createdAt: Date;
  updatedAt: Date;
  preferences?: UserPreferences;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export type SubscriptionTier = 'free' | 'starter' | 'professional' | 'enterprise';

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  currency: string;
  timezone: string;
  notifications: NotificationPreferences;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  sms: boolean;
  trading: {
    priceAlerts: boolean;
    stopLoss: boolean;
    takeProfit: boolean;
  };
}

export interface Trade {
  id: string;
  userId: string;
  symbol: string;
  type: 'buy' | 'sell';
  quantity: number;
  price: number;
  total: number;
  commission: number;
  executedAt: Date;
  notes?: string;
  tags?: string[];
  platformId?: string;
}

export interface Portfolio {
  userId: string;
  totalValue: number;
  dayChange: number;
  dayChangePercent: number;
  positions: Position[];
  cash: number;
  lastUpdated: Date;
}

export interface Position {
  symbol: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  value: number;
  dayChange: number;
  totalChange: number;
  percentChange: number;
}

export interface Analytics {
  winRate: number;
  totalTrades: number;
  profitableTrades: number;
  totalPnL: number;
  averageWin: number;
  averageLoss: number;
  bestTrade: Trade | null;
  worstTrade: Trade | null;
  sharpeRatio: number;
  maxDrawdown: number;
}

export interface ApiError {
  message: string;
  code: string;
  statusCode: number;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface FilterOptions {
  startDate?: Date;
  endDate?: Date;
  symbols?: string[];
  tags?: string[];
  minAmount?: number;
  maxAmount?: number;
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string;
    borderColor?: string;
  }[];
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  actionUrl?: string;
}

export interface SupportTicket {
  id: string;
  subject: string;
  description: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  createdAt: Date;
  updatedAt: Date;
  messages: TicketMessage[];
}

export interface TicketMessage {
  id: string;
  ticketId: string;
  userId: string;
  message: string;
  attachments?: string[];
  createdAt: Date;
}

export interface KnowledgeBaseArticle {
  id: string;
  title: string;
  slug: string;
  content: string;
  category: string;
  tags: string[];
  views: number;
  helpful: number;
  notHelpful: number;
  lastUpdated: Date;
}

// Form validation types
export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any) => boolean;
  message: string;
}

export interface FormField<T = any> {
  value: T;
  error: string | null;
  touched: boolean;
  rules: ValidationRule[];
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: ApiError;
  metadata?: {
    timestamp: Date;
    requestId: string;
    version: string;
  };
}

// WebSocket types
export interface WSMessage {
  type: 'trade' | 'price' | 'notification' | 'system';
  data: any;
  timestamp: Date;
}

// Export enums
export enum TradeStatus {
  PENDING = 'pending',
  EXECUTED = 'executed',
  CANCELLED = 'cancelled',
  FAILED = 'failed'
}

export enum OrderType {
  MARKET = 'market',
  LIMIT = 'limit',
  STOP = 'stop',
  STOP_LIMIT = 'stop_limit'
}