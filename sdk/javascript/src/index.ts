/**
 * TradeSense JavaScript/TypeScript SDK
 * Official JavaScript client for the TradeSense API
 */

export interface TradeSenseConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
  retries?: number;
}

export interface Trade {
  id?: string;
  symbol: string;
  entry_date: string;
  exit_date?: string;
  entry_price: number;
  exit_price?: number;
  quantity: number;
  trade_type: 'long' | 'short';
  profit_loss?: number;
  commission?: number;
  notes?: string;
  tags?: string[];
  strategy?: string;
  created_at?: string;
  updated_at?: string;
}

export interface JournalEntry {
  id?: string;
  title: string;
  content: string;
  mood?: string;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface AnalyticsOverview {
  total_trades: number;
  total_pnl: number;
  win_rate: number;
  profit_factor: number;
  average_win: number;
  average_loss: number;
  best_trade: number;
  worst_trade: number;
  total_commission: number;
  net_pnl: number;
}

export interface ExperimentAssignment {
  experiment_id: string;
  variant_id: string;
  variant_name: string;
  config: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export class TradeSenseError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: any
  ) {
    super(message);
    this.name = 'TradeSenseError';
  }
}

export class AuthenticationError extends TradeSenseError {
  constructor(message: string) {
    super(message, 401);
    this.name = 'AuthenticationError';
  }
}

class BaseClient {
  protected apiKey: string;
  protected baseUrl: string;
  protected timeout: number;
  protected retries: number;

  constructor(config: TradeSenseConfig) {
    this.apiKey = config.apiKey || process.env.TRADESENSE_API_KEY || '';
    if (!this.apiKey) {
      throw new AuthenticationError('API key is required');
    }

    this.baseUrl = (config.baseUrl || 'https://api.tradesense.com').replace(/\/$/, '');
    this.timeout = config.timeout || 30000;
    this.retries = config.retries || 3;
  }

  protected async request<T>(
    method: string,
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json',
      'User-Agent': 'TradeSense-JS-SDK/1.0.0',
      ...options.headers,
    };

    let lastError: Error | null = null;
    for (let attempt = 0; attempt <= this.retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        const response = await fetch(url, {
          ...options,
          method,
          headers,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          if (response.status === 401) {
            throw new AuthenticationError('Invalid API key or authentication failed');
          }

          let errorMessage = `API request failed: ${response.statusText}`;
          try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorMessage;
          } catch {}

          throw new TradeSenseError(errorMessage, response.status);
        }

        if (response.status === 204) {
          return {} as T;
        }

        return await response.json();
      } catch (error: any) {
        lastError = error;
        
        if (error.name === 'AbortError') {
          throw new TradeSenseError('Request timeout', 408);
        }
        
        if (error instanceof TradeSenseError || attempt === this.retries) {
          throw error;
        }
        
        // Wait before retry (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      }
    }

    throw lastError || new TradeSenseError('Request failed after retries');
  }

  protected buildQueryString(params: Record<string, any>): string {
    const cleaned = Object.entries(params)
      .filter(([_, value]) => value !== undefined && value !== null)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
    
    return cleaned.length > 0 ? `?${cleaned.join('&')}` : '';
  }
}

export class TradesClient extends BaseClient {
  async list(params?: {
    start_date?: string;
    end_date?: string;
    symbol?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<Trade>> {
    const queryString = this.buildQueryString(params || {});
    return this.request<PaginatedResponse<Trade>>('GET', `/api/v1/trades${queryString}`);
  }

  async create(trade: Omit<Trade, 'id' | 'created_at' | 'updated_at'>): Promise<Trade> {
    return this.request<Trade>('POST', '/api/v1/trades', {
      body: JSON.stringify(trade),
    });
  }

  async get(tradeId: string): Promise<Trade> {
    return this.request<Trade>('GET', `/api/v1/trades/${tradeId}`);
  }

  async update(tradeId: string, updates: Partial<Trade>): Promise<Trade> {
    return this.request<Trade>('PUT', `/api/v1/trades/${tradeId}`, {
      body: JSON.stringify(updates),
    });
  }

  async delete(tradeId: string): Promise<void> {
    await this.request<void>('DELETE', `/api/v1/trades/${tradeId}`);
  }

  async bulkCreate(trades: Omit<Trade, 'id' | 'created_at' | 'updated_at'>[]): Promise<{
    created: number;
    errors: any[];
  }> {
    return this.request('POST', '/api/v1/trades/bulk', {
      body: JSON.stringify({ trades }),
    });
  }

  async importCSV(file: File | Blob, broker: string = 'generic'): Promise<{
    imported: number;
    errors: any[];
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('broker', broker);

    return this.request('POST', '/api/v1/trades/import', {
      body: formData,
      headers: {
        // Remove Content-Type to let browser set it with boundary
      },
    });
  }
}

export class AnalyticsClient extends BaseClient {
  async overview(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<AnalyticsOverview> {
    const queryString = this.buildQueryString(params || {});
    return this.request<AnalyticsOverview>('GET', `/api/v1/analytics/overview${queryString}`);
  }

  async performance(timeframe: 'day' | 'week' | 'month' | 'year' | 'all' = 'all'): Promise<any> {
    return this.request('GET', `/api/v1/analytics/performance?timeframe=${timeframe}`);
  }

  async winLoss(): Promise<any> {
    return this.request('GET', '/api/v1/analytics/win-loss');
  }

  async bySymbol(): Promise<any[]> {
    return this.request('GET', '/api/v1/analytics/by-symbol');
  }

  async byDayOfWeek(): Promise<any> {
    return this.request('GET', '/api/v1/analytics/by-day');
  }

  async byTimeOfDay(): Promise<any> {
    return this.request('GET', '/api/v1/analytics/by-hour');
  }

  async streaks(): Promise<any> {
    return this.request('GET', '/api/v1/analytics/streaks');
  }

  async riskMetrics(): Promise<any> {
    return this.request('GET', '/api/v1/analytics/risk');
  }
}

export class JournalClient extends BaseClient {
  async list(params?: {
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<JournalEntry>> {
    const queryString = this.buildQueryString(params || {});
    return this.request<PaginatedResponse<JournalEntry>>('GET', `/api/v1/journal${queryString}`);
  }

  async create(entry: Omit<JournalEntry, 'id' | 'created_at' | 'updated_at'>): Promise<JournalEntry> {
    return this.request<JournalEntry>('POST', '/api/v1/journal', {
      body: JSON.stringify(entry),
    });
  }

  async get(entryId: string): Promise<JournalEntry> {
    return this.request<JournalEntry>('GET', `/api/v1/journal/${entryId}`);
  }

  async update(entryId: string, updates: Partial<JournalEntry>): Promise<JournalEntry> {
    return this.request<JournalEntry>('PUT', `/api/v1/journal/${entryId}`, {
      body: JSON.stringify(updates),
    });
  }

  async delete(entryId: string): Promise<void> {
    await this.request<void>('DELETE', `/api/v1/journal/${entryId}`);
  }

  async search(query: string): Promise<JournalEntry[]> {
    return this.request<JournalEntry[]>('GET', `/api/v1/journal/search?q=${encodeURIComponent(query)}`);
  }
}

export class AccountClient extends BaseClient {
  async profile(): Promise<any> {
    return this.request('GET', '/api/v1/account/profile');
  }

  async updateProfile(updates: any): Promise<any> {
    return this.request('PUT', '/api/v1/account/profile', {
      body: JSON.stringify(updates),
    });
  }

  async subscription(): Promise<any> {
    return this.request('GET', '/api/v1/subscription/status');
  }

  async usage(): Promise<any> {
    return this.request('GET', '/api/v1/account/usage');
  }

  async apiKeys(): Promise<any[]> {
    return this.request('GET', '/api/v1/account/api-keys');
  }

  async createApiKey(name: string, permissions?: string[]): Promise<any> {
    return this.request('POST', '/api/v1/account/api-keys', {
      body: JSON.stringify({ name, permissions }),
    });
  }

  async revokeApiKey(keyId: string): Promise<void> {
    await this.request('DELETE', `/api/v1/account/api-keys/${keyId}`);
  }
}

export class ExperimentsClient extends BaseClient {
  async getAssignments(): Promise<ExperimentAssignment[]> {
    return this.request<ExperimentAssignment[]>('GET', '/api/v1/experiments/assignments');
  }

  async getVariant(experimentId: string): Promise<ExperimentAssignment | null> {
    return this.request<ExperimentAssignment | null>('GET', `/api/v1/experiments/assignment/${experimentId}`);
  }

  async trackConversion(
    experimentId: string,
    metricId: string,
    value: number = 1.0,
    metadata?: Record<string, any>
  ): Promise<void> {
    await this.request('POST', '/api/v1/experiments/track', {
      body: JSON.stringify({
        experiment_id: experimentId,
        metric_id: metricId,
        value,
        metadata,
      }),
    });
  }
}

export class TradeSenseClient {
  public trades: TradesClient;
  public analytics: AnalyticsClient;
  public journal: JournalClient;
  public account: AccountClient;
  public experiments: ExperimentsClient;

  constructor(config: TradeSenseConfig) {
    this.trades = new TradesClient(config);
    this.analytics = new AnalyticsClient(config);
    this.journal = new JournalClient(config);
    this.account = new AccountClient(config);
    this.experiments = new ExperimentsClient(config);
  }
}

// Default export
export default TradeSenseClient;

// Convenience function
export function createClient(config: TradeSenseConfig): TradeSenseClient {
  return new TradeSenseClient(config);
}