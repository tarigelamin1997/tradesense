import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MemoryCache, ApiCache, StorageCache, PerformanceMonitor } from '$lib/utils/cache';

describe('MemoryCache', () => {
  let cache: MemoryCache<string>;

  beforeEach(() => {
    cache = new MemoryCache({ ttl: 1000, maxSize: 3 });
  });

  it('should store and retrieve values', () => {
    cache.set('key1', 'value1');
    expect(cache.get('key1')).toBe('value1');
  });

  it('should expire values after TTL', async () => {
    cache.set('key1', 'value1', 100); // 100ms TTL
    expect(cache.get('key1')).toBe('value1');
    
    await new Promise(resolve => setTimeout(resolve, 150));
    expect(cache.get('key1')).toBeUndefined();
  });

  it('should enforce max size with LRU eviction', () => {
    const onEvict = vi.fn();
    cache = new MemoryCache({ maxSize: 3, onEvict });

    cache.set('key1', 'value1');
    cache.set('key2', 'value2');
    cache.set('key3', 'value3');
    
    // Should evict key1 (oldest)
    cache.set('key4', 'value4');
    
    expect(cache.has('key1')).toBe(false);
    expect(cache.has('key4')).toBe(true);
    expect(onEvict).toHaveBeenCalledWith('key1', 'value1');
  });

  it('should update LRU order on get', () => {
    cache.set('key1', 'value1');
    cache.set('key2', 'value2');
    cache.set('key3', 'value3');
    
    // Access key1 to make it most recently used
    cache.get('key1');
    
    // Should evict key2 (now oldest)
    cache.set('key4', 'value4');
    
    expect(cache.has('key1')).toBe(true);
    expect(cache.has('key2')).toBe(false);
  });

  it('should delete entries', () => {
    cache.set('key1', 'value1');
    expect(cache.delete('key1')).toBe(true);
    expect(cache.has('key1')).toBe(false);
    expect(cache.delete('key1')).toBe(false);
  });

  it('should clear all entries', () => {
    cache.set('key1', 'value1');
    cache.set('key2', 'value2');
    
    cache.clear();
    expect(cache.size()).toBe(0);
    expect(cache.has('key1')).toBe(false);
    expect(cache.has('key2')).toBe(false);
  });

  it('should cleanup expired entries', () => {
    cache.set('key1', 'value1', 100);
    cache.set('key2', 'value2', 1000);
    
    // Wait for key1 to expire
    vi.advanceTimersByTime(150);
    cache.cleanup();
    
    expect(cache.has('key1')).toBe(false);
    expect(cache.has('key2')).toBe(true);
  });
});

describe('ApiCache', () => {
  let apiCache: ApiCache;

  beforeEach(() => {
    apiCache = new ApiCache();
    vi.clearAllMocks();
  });

  it('should cache API responses', async () => {
    const fetcher = vi.fn().mockResolvedValue({ data: 'test' });
    
    // First call should fetch
    const result1 = await apiCache.fetch('key1', fetcher);
    expect(result1).toEqual({ data: 'test' });
    expect(fetcher).toHaveBeenCalledTimes(1);
    
    // Second call should use cache
    const result2 = await apiCache.fetch('key1', fetcher);
    expect(result2).toEqual({ data: 'test' });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it('should deduplicate concurrent requests', async () => {
    const fetcher = vi.fn().mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ data: 'test' }), 100))
    );
    
    // Make multiple concurrent requests
    const promises = [
      apiCache.fetch('key1', fetcher),
      apiCache.fetch('key1', fetcher),
      apiCache.fetch('key1', fetcher)
    ];
    
    const results = await Promise.all(promises);
    
    // Should only call fetcher once
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(results).toEqual([
      { data: 'test' },
      { data: 'test' },
      { data: 'test' }
    ]);
  });

  it('should handle fetch errors', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('Fetch failed'));
    
    await expect(apiCache.fetch('key1', fetcher)).rejects.toThrow('Fetch failed');
    
    // Should not cache errors
    await expect(apiCache.fetch('key1', fetcher)).rejects.toThrow('Fetch failed');
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it('should invalidate cache by pattern', async () => {
    const fetcher1 = vi.fn().mockResolvedValue({ data: 'user1' });
    const fetcher2 = vi.fn().mockResolvedValue({ data: 'user2' });
    const fetcher3 = vi.fn().mockResolvedValue({ data: 'post1' });
    
    // Cache multiple entries
    await apiCache.fetch('users:1', fetcher1);
    await apiCache.fetch('users:2', fetcher2);
    await apiCache.fetch('posts:1', fetcher3);
    
    // Invalidate all user entries
    apiCache.invalidate(/^users:/);
    
    // User entries should be refetched
    await apiCache.fetch('users:1', fetcher1);
    await apiCache.fetch('users:2', fetcher2);
    expect(fetcher1).toHaveBeenCalledTimes(2);
    expect(fetcher2).toHaveBeenCalledTimes(2);
    
    // Post entry should still be cached
    await apiCache.fetch('posts:1', fetcher3);
    expect(fetcher3).toHaveBeenCalledTimes(1);
  });

  it('should invalidate all cache when no pattern provided', async () => {
    const fetcher = vi.fn().mockResolvedValue({ data: 'test' });
    
    await apiCache.fetch('key1', fetcher);
    apiCache.invalidate();
    
    await apiCache.fetch('key1', fetcher);
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
});

describe('StorageCache', () => {
  let storageCache: StorageCache;
  let mockStorage: Storage;

  beforeEach(() => {
    const storage = new Map();
    mockStorage = {
      length: 0,
      clear: vi.fn(() => storage.clear()),
      getItem: vi.fn((key: string) => storage.get(key) || null),
      setItem: vi.fn((key: string, value: string) => {
        storage.set(key, value);
        (mockStorage as any).length = storage.size;
      }),
      removeItem: vi.fn((key: string) => {
        storage.delete(key);
        (mockStorage as any).length = storage.size;
      }),
      key: vi.fn((index: number) => Array.from(storage.keys())[index] || null)
    };

    global.localStorage = mockStorage;
    storageCache = new StorageCache('test:');
  });

  it('should store and retrieve values from localStorage', () => {
    storageCache.set('key1', { data: 'test' });
    const retrieved = storageCache.get<{ data: string }>('key1');
    
    expect(retrieved).toEqual({ data: 'test' });
    expect(mockStorage.setItem).toHaveBeenCalledWith(
      'test:key1',
      expect.stringContaining('"data":"test"')
    );
  });

  it('should expire values after TTL', () => {
    const now = Date.now();
    vi.setSystemTime(now);
    
    storageCache.set('key1', 'value1', 100);
    
    // Should retrieve before expiry
    expect(storageCache.get('key1')).toBe('value1');
    
    // Move time forward
    vi.setSystemTime(now + 150);
    
    // Should be expired
    expect(storageCache.get('key1')).toBeUndefined();
    expect(mockStorage.removeItem).toHaveBeenCalledWith('test:key1');
  });

  it('should handle storage quota exceeded', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    
    // Simulate quota exceeded
    mockStorage.setItem = vi.fn(() => {
      throw new Error('QuotaExceededError');
    });
    
    storageCache.set('key1', 'value1');
    
    expect(consoleSpy).toHaveBeenCalledWith(
      'Storage quota exceeded, clearing old entries'
    );
  });

  it('should handle corrupted data gracefully', () => {
    mockStorage.getItem = vi.fn(() => 'invalid json');
    
    expect(storageCache.get('key1')).toBeUndefined();
  });

  it('should clear all cache entries with prefix', () => {
    storageCache.set('key1', 'value1');
    storageCache.set('key2', 'value2');
    
    // Add entry with different prefix
    mockStorage.setItem('other:key', 'value');
    
    storageCache.clear();
    
    expect(mockStorage.removeItem).toHaveBeenCalledWith('test:key1');
    expect(mockStorage.removeItem).toHaveBeenCalledWith('test:key2');
    expect(mockStorage.removeItem).not.toHaveBeenCalledWith('other:key');
  });

  it('should cleanup expired entries', () => {
    const now = Date.now();
    vi.setSystemTime(now);
    
    // Set entries with different TTLs
    storageCache.set('key1', 'value1', 100);
    storageCache.set('key2', 'value2', 1000);
    
    // Move time forward
    vi.setSystemTime(now + 150);
    
    storageCache.cleanup();
    
    expect(mockStorage.removeItem).toHaveBeenCalledWith('test:key1');
    expect(mockStorage.removeItem).not.toHaveBeenCalledWith('test:key2');
  });
});

describe('PerformanceMonitor', () => {
  let monitor: PerformanceMonitor;

  beforeEach(() => {
    monitor = new PerformanceMonitor();
    vi.spyOn(performance, 'now').mockReturnValue(1000);
  });

  it('should mark and measure performance', () => {
    monitor.mark('start');
    
    vi.spyOn(performance, 'now').mockReturnValue(1250);
    const duration = monitor.measure('operation', 'start');
    
    expect(duration).toBe(250);
  });

  it('should calculate average durations', () => {
    // First operation
    monitor.mark('start1');
    vi.spyOn(performance, 'now').mockReturnValue(1100);
    monitor.measure('api-call', 'start1');
    
    // Second operation
    monitor.mark('start2');
    vi.spyOn(performance, 'now').mockReturnValue(1300);
    monitor.measure('api-call', 'start2');
    
    expect(monitor.getAverageDuration('api-call')).toBe(150);
  });

  it('should get metrics summary', () => {
    // Multiple measurements
    monitor.mark('start1');
    vi.spyOn(performance, 'now').mockReturnValue(1100);
    monitor.measure('api-call', 'start1');
    
    monitor.mark('start2');
    vi.spyOn(performance, 'now').mockReturnValue(1250);
    monitor.measure('api-call', 'start2');
    
    monitor.mark('render');
    vi.spyOn(performance, 'now').mockReturnValue(1300);
    monitor.measure('component-render', 'render');
    
    const metrics = monitor.getMetrics();
    
    expect(metrics['api-call']).toEqual({
      average: 125,
      count: 2,
      last: 150
    });
    
    expect(metrics['component-render']).toEqual({
      average: 50,
      count: 1,
      last: 50
    });
  });

  it('should limit stored measures to 100', () => {
    // Add 105 measures
    for (let i = 0; i < 105; i++) {
      monitor.mark(`start${i}`);
      vi.spyOn(performance, 'now').mockReturnValue(1000 + i * 10);
      monitor.measure('test', `start${i}`);
    }
    
    const metrics = monitor.getMetrics();
    expect(metrics['test'].count).toBe(100);
  });

  it('should clear all data', () => {
    monitor.mark('start');
    monitor.measure('test', 'start');
    
    monitor.clear();
    
    expect(monitor.getMetrics()).toEqual({});
    expect(monitor.getAverageDuration('test')).toBe(0);
  });

  it('should handle missing start marks', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    
    const duration = monitor.measure('test', 'nonexistent');
    
    expect(duration).toBe(0);
    expect(consoleSpy).toHaveBeenCalledWith('Start mark "nonexistent" not found');
  });
});