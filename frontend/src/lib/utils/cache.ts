interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

interface CacheOptions {
  ttl?: number; // Time to live in milliseconds
  maxSize?: number; // Maximum number of entries
  onEvict?: (key: string, value: any) => void;
}

export class MemoryCache<T = any> {
  private cache = new Map<string, CacheEntry<T>>();
  private accessOrder: string[] = [];
  private options: Required<CacheOptions>;

  constructor(options: CacheOptions = {}) {
    this.options = {
      ttl: 5 * 60 * 1000, // 5 minutes default
      maxSize: 100,
      onEvict: () => {},
      ...options
    };
  }

  set(key: string, value: T, ttl?: number): void {
    const expiresAt = Date.now() + (ttl || this.options.ttl);
    
    // Remove from access order if exists
    this.removeFromAccessOrder(key);
    
    // Add to cache
    this.cache.set(key, {
      data: value,
      timestamp: Date.now(),
      expiresAt
    });
    
    // Update access order
    this.accessOrder.push(key);
    
    // Enforce max size
    while (this.cache.size > this.options.maxSize) {
      const oldestKey = this.accessOrder.shift();
      if (oldestKey) {
        const entry = this.cache.get(oldestKey);
        this.cache.delete(oldestKey);
        if (entry) {
          this.options.onEvict(oldestKey, entry.data);
        }
      }
    }
  }

  get(key: string): T | undefined {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return undefined;
    }
    
    // Check if expired
    if (Date.now() > entry.expiresAt) {
      this.delete(key);
      return undefined;
    }
    
    // Update access order (LRU)
    this.removeFromAccessOrder(key);
    this.accessOrder.push(key);
    
    return entry.data;
  }

  has(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return false;
    
    if (Date.now() > entry.expiresAt) {
      this.delete(key);
      return false;
    }
    
    return true;
  }

  delete(key: string): boolean {
    const entry = this.cache.get(key);
    if (entry) {
      this.cache.delete(key);
      this.removeFromAccessOrder(key);
      this.options.onEvict(key, entry.data);
      return true;
    }
    return false;
  }

  clear(): void {
    for (const [key, entry] of this.cache.entries()) {
      this.options.onEvict(key, entry.data);
    }
    this.cache.clear();
    this.accessOrder = [];
  }

  size(): number {
    return this.cache.size;
  }

  // Clean up expired entries
  cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.delete(key);
      }
    }
  }

  private removeFromAccessOrder(key: string): void {
    const index = this.accessOrder.indexOf(key);
    if (index > -1) {
      this.accessOrder.splice(index, 1);
    }
  }
}

// API Response Cache with deduplication
export class ApiCache {
  private cache = new MemoryCache<any>();
  private pendingRequests = new Map<string, Promise<any>>();

  async fetch<T>(
    key: string,
    fetcher: () => Promise<T>,
    options?: { ttl?: number }
  ): Promise<T> {
    // Check cache first
    const cached = this.cache.get(key);
    if (cached !== undefined) {
      return cached as T;
    }

    // Check if request is already pending (deduplication)
    const pending = this.pendingRequests.get(key);
    if (pending) {
      return pending;
    }

    // Make request
    const promise = fetcher()
      .then(data => {
        this.cache.set(key, data, options?.ttl);
        this.pendingRequests.delete(key);
        return data;
      })
      .catch(error => {
        this.pendingRequests.delete(key);
        throw error;
      });

    this.pendingRequests.set(key, promise);
    return promise;
  }

  invalidate(pattern?: string | RegExp): void {
    if (!pattern) {
      this.cache.clear();
      return;
    }

    // Invalidate matching keys
    const regex = typeof pattern === 'string' 
      ? new RegExp(pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
      : pattern;

    for (const key of Array.from(this.cache['cache'].keys())) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }
}

// Browser Storage Cache (localStorage/sessionStorage)
export class StorageCache {
  private prefix: string;
  private storage: Storage;

  constructor(prefix = 'cache:', useSessionStorage = false) {
    this.prefix = prefix;
    this.storage = useSessionStorage ? sessionStorage : localStorage;
  }

  set<T>(key: string, value: T, ttl?: number): void {
    const fullKey = this.prefix + key;
    const entry: CacheEntry<T> = {
      data: value,
      timestamp: Date.now(),
      expiresAt: Date.now() + (ttl || 5 * 60 * 1000)
    };

    try {
      this.storage.setItem(fullKey, JSON.stringify(entry));
    } catch (e) {
      // Handle quota exceeded
      console.warn('Storage quota exceeded, clearing old entries');
      this.cleanup();
      try {
        this.storage.setItem(fullKey, JSON.stringify(entry));
      } catch {
        console.error('Failed to cache data');
      }
    }
  }

  get<T>(key: string): T | undefined {
    const fullKey = this.prefix + key;
    
    try {
      const item = this.storage.getItem(fullKey);
      if (!item) return undefined;

      const entry: CacheEntry<T> = JSON.parse(item);
      
      if (Date.now() > entry.expiresAt) {
        this.storage.removeItem(fullKey);
        return undefined;
      }

      return entry.data;
    } catch {
      return undefined;
    }
  }

  delete(key: string): void {
    this.storage.removeItem(this.prefix + key);
  }

  clear(): void {
    const keys = [];
    for (let i = 0; i < this.storage.length; i++) {
      const key = this.storage.key(i);
      if (key?.startsWith(this.prefix)) {
        keys.push(key);
      }
    }
    keys.forEach(key => this.storage.removeItem(key));
  }

  cleanup(): void {
    const now = Date.now();
    const keys = [];
    
    for (let i = 0; i < this.storage.length; i++) {
      const key = this.storage.key(i);
      if (key?.startsWith(this.prefix)) {
        keys.push(key);
      }
    }

    for (const key of keys) {
      try {
        const item = this.storage.getItem(key);
        if (item) {
          const entry: CacheEntry<any> = JSON.parse(item);
          if (now > entry.expiresAt) {
            this.storage.removeItem(key);
          }
        }
      } catch {
        // Remove corrupted entries
        this.storage.removeItem(key);
      }
    }
  }
}

// Create singleton instances
export const memoryCache = new MemoryCache();
export const apiCache = new ApiCache();
export const storageCache = new StorageCache();

// Performance monitoring
export class PerformanceMonitor {
  private marks = new Map<string, number>();
  private measures: Array<{ name: string; duration: number; timestamp: number }> = [];

  mark(name: string): void {
    this.marks.set(name, performance.now());
  }

  measure(name: string, startMark: string): number {
    const start = this.marks.get(startMark);
    if (!start) {
      console.warn(`Start mark "${startMark}" not found`);
      return 0;
    }

    const duration = performance.now() - start;
    this.measures.push({
      name,
      duration,
      timestamp: Date.now()
    });

    // Keep only last 100 measures
    if (this.measures.length > 100) {
      this.measures.shift();
    }

    return duration;
  }

  getAverageDuration(name: string): number {
    const relevantMeasures = this.measures.filter(m => m.name === name);
    if (relevantMeasures.length === 0) return 0;

    const sum = relevantMeasures.reduce((acc, m) => acc + m.duration, 0);
    return sum / relevantMeasures.length;
  }

  getMetrics(): Record<string, { average: number; count: number; last: number }> {
    const metrics: Record<string, { average: number; count: number; last: number }> = {};

    for (const measure of this.measures) {
      if (!metrics[measure.name]) {
        metrics[measure.name] = { average: 0, count: 0, last: 0 };
      }

      const metric = metrics[measure.name];
      metric.count++;
      metric.last = measure.duration;
      metric.average = this.getAverageDuration(measure.name);
    }

    return metrics;
  }

  clear(): void {
    this.marks.clear();
    this.measures = [];
  }
}

export const performanceMonitor = new PerformanceMonitor();